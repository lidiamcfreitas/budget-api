import firebase_admin
from firebase_admin import credentials, firestore
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("/Users/lidiafreitas/programming/keys/budgetapp-449511-firebase-adminsdk-fbsvc-80fc508f2e.json")
    firebase_admin.initialize_app(cred, {
        "projectId": "budgetapp-449511",
    })

db = firestore.client()

class Migration:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.backup_data = {}
        self.changes_made = []

    def backup_collection(self, collection_name: str) -> None:
        """Backup a collection before making changes"""
        logger.info(f"Backing up collection: {collection_name}")
        docs = db.collection(collection_name).stream()
        self.backup_data[collection_name] = {
            doc.id: doc.to_dict() for doc in docs
        }

    def save_backup(self, filename: str) -> None:
        """Save backup data to a file"""
        with open(filename, 'w') as f:
            json.dump(self.backup_data, f)
        logger.info(f"Backup saved to {filename}")

    def load_backup(self, filename: str) -> None:
        """Load backup data from a file"""
        with open(filename, 'r') as f:
            self.backup_data = json.load(f)
        logger.info(f"Backup loaded from {filename}")

    def migrate_categories(self) -> None:
        """
        Migrate categories:
        1. Add group_id field
        2. Move target fields from CategoryTarget
        3. Remove redundant fields
        """
        logger.info("Starting category migration")
        self.backup_collection("categories")
        self.backup_collection("categoryTargets")

        # Get all category targets for quick lookup
        target_docs = db.collection("categoryTargets").stream()
        targets_by_category = {
            doc.to_dict()["category_id"]: doc.to_dict()
            for doc in target_docs
        }

        # Get all category groups for mapping
        groups_ref = db.collection("categoryGroups").stream()
        groups_by_budget = {}
        for group in groups_ref:
            group_data = group.to_dict()
            budget_id = group_data["budget_id"]
            if budget_id not in groups_by_budget:
                groups_by_budget[budget_id] = []
            groups_by_budget[budget_id].append(group_data)

        batch = db.batch()
        categories_ref = db.collection("categories").stream()
        
        for cat_doc in categories_ref:
            cat_data = cat_doc.to_dict()
            cat_ref = db.collection("categories").document(cat_doc.id)
            
            # Find appropriate group for this category
            budget_id = cat_data["budget_id"]
            if budget_id in groups_by_budget:
                # Assign to first group if no better logic available
                group_id = groups_by_budget[budget_id][0]["group_id"]
            else:
                logger.warning(f"No group found for category {cat_doc.id} in budget {budget_id}")
                continue

            # Get target data if exists
            target_data = targets_by_category.get(cat_doc.id, {})

            # Update category document
            updated_data = {
                **cat_data,
                "group_id": group_id,
                "target_amount": target_data.get("target_amount"),
                "target_type": target_data.get("target_type"),
                "target_due_date": target_data.get("target_due_date")
            }

            if not self.dry_run:
                batch.set(cat_ref, updated_data)
                self.changes_made.append({
                    "collection": "categories",
                    "doc_id": cat_doc.id,
                    "change": "Updated with group_id and target data"
                })

        if not self.dry_run:
            batch.commit()
            logger.info("Category migration completed")
        else:
            logger.info("Dry run - no changes made")

    def migrate_transactions(self) -> None:
        """
        Migrate transactions:
        1. Remove redundant budget_id and user_id
        2. Add denormalized fields
        """
        logger.info("Starting transaction migration")
        self.backup_collection("transactions")

        # Get all accounts for quick lookup
        accounts_ref = db.collection("accounts").stream()
        accounts = {
            doc.id: doc.to_dict() for doc in accounts_ref
        }

        # Get all categories for quick lookup
        categories_ref = db.collection("categories").stream()
        categories = {
            doc.id: doc.to_dict() for doc in categories_ref
        }

        batch = db.batch()
        transactions_ref = db.collection("transactions").stream()

        for trans_doc in transactions_ref:
            trans_data = trans_doc.to_dict()
            trans_ref = db.collection("transactions").document(trans_doc.id)

            # Get account and category data
            account = accounts.get(trans_data["account_id"], {})
            category = categories.get(trans_data.get("category_id", ""), {})

            # Remove redundant fields and add denormalized ones
            updated_data = {
                "transaction_id": trans_doc.id,
                "account_id": trans_data["account_id"],
                "amount": trans_data["amount"],
                "date": trans_data["date"],
                "payee": trans_data.get("payee"),
                "category_id": trans_data.get("category_id"),
                "cleared": trans_data.get("cleared", False),
                "notes": trans_data.get("notes"),
                "pending": trans_data.get("pending", False),
                "account_name": account.get("name", "Unknown Account"),
                "category_name": category.get("name")
            }

            if not self.dry_run:
                batch.set(trans_ref, updated_data)
                self.changes_made.append({
                    "collection": "transactions",
                    "doc_id": trans_doc.id,
                    "change": "Updated schema and added denormalized fields"
                })

        if not self.dry_run:
            batch.commit()
            logger.info("Transaction migration completed")
        else:
            logger.info("Dry run - no changes made")

    def migrate_payees(self) -> None:
        """
        Migrate payees:
        1. Add budget_id field
        """
        logger.info("Starting payee migration")
        self.backup_collection("payees")

        # Get all transactions to determine budget_id for payees
        transactions_ref = db.collection("transactions").stream()
        payee_budgets = {}
        
        for trans in transactions_ref:
            trans_data = trans.to_dict()
            if trans_data.get("payee"):
                account = db.collection("accounts").document(trans_data["account_id"]).get()
                if account.exists:
                    budget_id = account.to_dict()["budget_id"]
                    payee_budgets[trans_data["payee"]] = budget_id

        batch = db.batch()
        payees_ref = db.collection("payees").stream()

        for payee_doc in payees_ref:
            payee_data = payee_doc.to_dict()
            payee_ref = db.collection("payees").document(payee_doc.id)

            budget_id = payee_budgets.get(payee_data["name"])
            if not budget_id:
                logger.warning(f"Could not determine budget_id for payee {payee_doc.id}")
                continue

            updated_data = {
                **payee_data,
                "budget_id": budget_id
            }

            if not self.dry_run:
                batch.set(payee_ref, updated_data)
                self.changes_made.append({
                    "collection": "payees",
                    "doc_id": payee_doc.id,
                    "change": "Added budget_id"
                })

        if not self.dry_run:
            batch.commit()
            logger.info("Payee migration completed")
        else:
            logger.info("Dry run - no changes made")

    def rollback(self) -> None:
        """Rollback all changes using backup data"""
        if not self.backup_data:
            logger.error("No backup data available for rollback")
            return

        logger.info("Starting rollback")
        batch = db.batch()

        for collection, docs in self.backup_data.items():
            for doc_id, data in docs.items():
                doc_ref = db.collection(collection).document(doc_id)
                batch.set(doc_ref, data)

        batch.commit()
        logger.info("Rollback completed")

def main():
    parser = argparse.ArgumentParser(description='Firestore Schema Migration Tool')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--backup-file', type=str, help='Backup file path')
    parser.add_argument('--rollback', action='store_true', help='Rollback changes using backup file')
    args = parser.parse_args()

    migration = Migration(dry_run=args.dry_run)

    if args.rollback and args.backup_file:
        migration.load_backup(args.backup_file)
        migration.rollback()
        return

    try:
        # Perform migrations
        migration.migrate_categories()
        migration.migrate_transactions()
        migration.migrate_payees()

        # Save backup if not a dry run
        if not args.dry_run and args.backup_file:
            migration.save_backup(args.backup_file)

        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if not args.dry_run:
            logger.info("Attempting rollback...")
            migration.rollback()
        sys.exit(1)

if __name__ == "__main__":
    main()
