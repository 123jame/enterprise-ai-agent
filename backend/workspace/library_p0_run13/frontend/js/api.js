/**
 * Library P0 Run13 - API Client
 * 
 * Provides helper functions for all backend API calls.
 * All functions return Promise with parsed JSON response.
 */

const Api = {
    /**
     * Base fetch wrapper with error handling.
     */
    async _request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };

        const config = {
            headers: { ...defaultHeaders, ...options.headers },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                const errorMsg = data.detail || data.message || `请求失败 (${response.status})`;
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('无法连接到服务器，请检查后端是否启动');
            }
            throw error;
        }
    },

    // ==================== Books API ====================

    books: {
        /**
         * Search books with optional filters.
         * @param {Object} params - { keyword, category, is_active, page, page_size }
         */
        search(params = {}) {
            const query = new URLSearchParams();
            if (params.keyword) query.set('keyword', params.keyword);
            if (params.category) query.set('category', params.category);
            if (params.is_active !== undefined && params.is_active !== null) {
                query.set('is_active', params.is_active);
            }
            query.set('page', params.page || 1);
            query.set('page_size', params.page_size || CONFIG.DEFAULT_PAGE_SIZE);
            return Api._request(`/api/books/?${query.toString()}`);
        },

        /**
         * Get a single book by ID.
         */
        get(bookId) {
            return Api._request(`/api/books/${bookId}`);
        },

        /**
         * Create a new book.
         */
        create(data) {
            return Api._request('/api/books/', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        /**
         * Update an existing book.
         */
        update(bookId, data) {
            return Api._request(`/api/books/${bookId}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },

        /**
         * Deactivate a book (take offline).
         */
        deactivate(bookId) {
            return Api._request(`/api/books/${bookId}/deactivate`, {
                method: 'PATCH',
            });
        },

        /**
         * Activate a book (put back online).
         */
        activate(bookId) {
            return Api._request(`/api/books/${bookId}/activate`, {
                method: 'PATCH',
            });
        },
    },

    // ==================== Readers API ====================

    readers: {
        /**
         * Search readers with optional keyword.
         */
        search(params = {}) {
            const query = new URLSearchParams();
            if (params.keyword) query.set('keyword', params.keyword);
            query.set('page', params.page || 1);
            query.set('page_size', params.page_size || CONFIG.DEFAULT_PAGE_SIZE);
            return Api._request(`/api/readers/?${query.toString()}`);
        },

        /**
         * Get a single reader by ID.
         */
        get(readerId) {
            return Api._request(`/api/readers/${readerId}`);
        },

        /**
         * Create a new reader.
         */
        create(data) {
            return Api._request('/api/readers/', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        /**
         * Update a reader (including activate/freeze).
         */
        update(readerId, data) {
            return Api._request(`/api/readers/${readerId}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
    },

    // ==================== Borrowings API ====================

    borrowings: {
        /**
         * Borrow a book.
         * @param {Object} data - { book_id, reader_id }
         */
        borrow(data) {
            return Api._request('/api/borrowings/borrow', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        /**
         * Return a book.
         * @param {Object} data - { borrowing_id }
         */
        returnBook(data) {
            return Api._request('/api/borrowings/return', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        /**
         * Get active borrowings for a reader.
         */
        getReaderActiveBorrowings(readerId) {
            return Api._request(`/api/borrowings/reader/${readerId}`);
        },
    },

    // ==================== Statistics API ====================

    stats: {
        /**
         * Get book statistics.
         */
        books() {
            return Api._request('/api/stats/books');
        },

        /**
         * Get reader statistics.
         */
        readers() {
            return Api._request('/api/stats/readers');
        },

        /**
         * Get popular books ranking.
         * @param {number} limit - Number of books to return.
         */
        popularBooks(limit = 10) {
            return Api._request(`/api/stats/popular-books?limit=${limit}`);
        },

        /**
         * Get overdue borrowings.
         */
        overdueBorrowings(params = {}) {
            const query = new URLSearchParams();
            query.set('page', params.page || 1);
            query.set('page_size', params.page_size || 20);
            return Api._request(`/api/stats/overdue?${query.toString()}`);
        },
    },

    // ==================== Health Check ====================

    health() {
        return Api._request('/api/health');
    },
};
