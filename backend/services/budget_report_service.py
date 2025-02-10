from datetime import datetime
from typing import List, Optional
import logging
from decimal import Decimal
from firebase_admin import firestore
from pydantic import BaseModel, field_validator
from .base_service import BaseService
from .budget_service import BudgetService
from .category_service import CategoryService
from .transaction_service import TransactionService
from models import Budget, Transaction, Category

class BudgetPeriod(BaseModel):
    year: int
    month: int

    @field_validator('month')
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v

class BudgetSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal

class CategoryTotal(BaseModel):
    category_id: str
    category_name: str
    total_amount: Decimal
    budget_amount: Optional[Decimal] = None
    percentage_used: Optional[float] = None

class MonthlyBudgetReport(BaseModel):
    budget: Budget
    period: BudgetPeriod
    transactions: List[Transaction]
    category_totals: List[CategoryTotal]
    summary: BudgetSummary

logger = logging.getLogger(__name__)

class BudgetReportService(BaseService):
    """Service for generating cross-entity budget reports and aggregated data."""

    def __init__(
        self,
        db: firestore.Client,
        budget_service: BudgetService,
        category_service: CategoryService,
        transaction_service: TransactionService
    ):
        """
        Initialize the BudgetReportService with required dependencies.

        Args:
            db: Firestore client instance
            budget_service: Instance of BudgetService
            category_service: Instance of CategoryService
            transaction_service: Instance of TransactionService
        """
        super().__init__()
        self.db = db
        self.budget_service = budget_service
        self.category_service = category_service
        self.transaction_service = transaction_service

    async def get_monthly_budget_data(
        self, 
        budget_id: str, 
        year: int,
        month: int
    ) -> MonthlyBudgetReport:
        """
        Get aggregated budget data for a specific month.

        Args:
            budget_id: The ID of the budget
            year: The year for which to get data
            month: The month for which to get data (1-12)

        Returns:
            Dictionary containing aggregated budget data including:
            - Budget details
            - Transactions for the month
            - Category totals
            - Overall totals

        Raises:
            ValueError: If the budget_id is invalid or dates are invalid
            FirestoreError: If there's an error accessing the database
        """
        try:
            logger.info(f"Fetching monthly budget data for budget {budget_id} - {year}/{month}")
            
            # Validate input
            if not budget_id:
                raise ValueError("Budget ID is required")
            if not 1 <= month <= 12:
                raise ValueError("Month must be between 1 and 12")
            
            # Get budget details
            budget = await self.budget_service.get_budget(budget_id)
            if not budget:
                raise ValueError(f"Budget not found: {budget_id}")

            # Get all relevant data
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            transactions = await self.transaction_service.get_transactions_for_period(
                budget_id, start_date, end_date
            )
            categories = await self.category_service.get_categories_for_budget(budget_id)
            
            # Calculate totals by category
            category_totals = self._calculate_category_totals(transactions, categories)
            
            # Calculate overall totals
            total_income = Decimal(str(sum(t.amount for t in transactions if t.amount > 0)))
            total_expenses = Decimal(str(sum(t.amount for t in transactions if t.amount < 0)))
            
            return MonthlyBudgetReport(
                budget=budget,
                period=BudgetPeriod(year=year, month=month),
                transactions=transactions,
                category_totals=category_totals,
                summary=BudgetSummary(
                    total_income=total_income,
                    total_expenses=abs(total_expenses),
                    net=total_income + total_expenses
                )
            )
            
        except ValueError as e:
            logger.error(f"Validation error in get_monthly_budget_data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting monthly budget data: {str(e)}")
            raise

    def _calculate_category_totals(
        self,
        transactions: List[Transaction],
        categories: List[Category]
    ) -> List[CategoryTotal]:
        """
        Calculate total amounts for each category.

        Args:
            transactions: List of transactions for the period
            categories: List of categories in the budget

        Returns:
            Dictionary mapping category IDs to their total amounts
        """
        category_amounts = {cat.id: Decimal('0') for cat in categories}
        category_name_map = {cat.id: cat.name for cat in categories}
        
        for transaction in transactions:
            if transaction.category_id in category_amounts:
                category_amounts[transaction.category_id] += Decimal(str(transaction.amount))
        
        return [
            CategoryTotal(
                category_id=cat_id,
                category_name=category_name_map[cat_id],
                total_amount=amount
            )
            for cat_id, amount in category_amounts.items()
        ]

