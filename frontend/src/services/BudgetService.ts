import axios, { AxiosInstance, AxiosError } from 'axios';
import { Budget, BudgetCreate, BudgetUpdate } from '../types/budget';
import { inject, injectable } from 'tsyringe';

export class ApiError extends Error {
constructor(
    message: string,
    public status?: number,
    public code?: string
) {
    super(message);
    this.name = 'ApiError';
}
}

@injectable()
export class BudgetService {
private readonly api: AxiosInstance;

constructor() {
    this.api = axios.create({
    baseURL: `${import.meta.env.VITE_API_BASE_URL}/budgets`,
    headers: {
        'Content-Type': 'application/json'
    }
    });
}

/**
* Create a new budget
* @param budget The budget data to create
* @returns The created budget
* @throws {ApiError} If the creation fails
*/
async create(budget: BudgetCreate): Promise<Budget> {
    try {
    const response = await this.api.post<Budget>('/', budget);
    return response.data;
    } catch (error) {
    this.handleError(error as AxiosError);
    }
}

/**
* Get a list of all budgets for the current user
* @returns Array of budgets
* @throws {ApiError} If the fetch fails
*/
async list(): Promise<Budget[]> {
    try {
    const response = await this.api.get<Budget[]>('/');
    return response.data;
    } catch (error) {
    this.handleError(error as AxiosError);
    }
}

/**
* Get a specific budget by ID
* @param id The budget ID
* @returns The budget data
* @throws {ApiError} If the fetch fails
*/
async get(id: string): Promise<Budget> {
    try {
    const response = await this.api.get<Budget>(`/${id}`);
    return response.data;
    } catch (error) {
    this.handleError(error as AxiosError);
    }
}

/**
* Update an existing budget
* @param id The budget ID
* @param update The update data
* @returns The updated budget
* @throws {ApiError} If the update fails
*/
async update(id: string, update: BudgetUpdate): Promise<Budget> {
    try {
    const response = await this.api.put<Budget>(`/${id}`, update);
    return response.data;
    } catch (error) {
    this.handleError(error as AxiosError);
    }
}

/**
* Delete a budget
* @param id The budget ID
* @returns void
* @throws {ApiError} If the deletion fails
*/
async delete(id: string): Promise<void> {
    try {
    await this.api.delete(`/${id}`);
    } catch (error) {
    this.handleError(error as AxiosError);
    }
}

/**
* Handle API errors and transform them into ApiError instances
* @param error The axios error
* @throws {ApiError} A transformed API error
*/
private handleError(error: AxiosError): never {
    if (error.response) {
    throw new ApiError(
        error.response.data?.message || 'An error occurred',
        error.response.status,
        error.response.data?.code
    );
    }
    
    if (error.request) {
    throw new ApiError('No response received from server');
    }
    
    throw new ApiError('Failed to make request');
}
}

