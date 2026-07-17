/**
 * Library P0 Run13 - 图书管理系统前端应用
 * Vue 3 SPA with all feature modules
 */
const { createApp, ref, reactive, computed, onMounted, nextTick } = Vue;

// ==================== Utility Functions ====================
const Utils = {
    formatDate(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toISOString().split('T')[0];
    },
    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString('zh-CN', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit',
        });
    },
    getOverdueDays(dueDateStr) {
        const due = new Date(dueDateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return Math.ceil((today - due) / (1000 * 60 * 60 * 24));
    },
    showToast(message, type = 'success') {
        const toastEl = document.getElementById('toast-notification');
        if (!toastEl) return;
        const titles = { success: '成功', error: '错误', warning: '提示', info: '信息' };
        document.getElementById('toast-title').textContent = titles[type] || '通知';
        document.getElementById('toast-message').textContent = message;
        const borderMap = { error: 'danger', warning: 'warning' };
        toastEl.className = `toast border-${borderMap[type] || 'success'}`;
        new bootstrap.Toast(toastEl, { delay: 3000 }).show();
    },
    showConfirm(title, message) {
        return new Promise((resolve) => {
            const modalEl = document.getElementById('confirmModal');
            if (!modalEl) { resolve(confirm(message)); return; }
            document.getElementById('confirmModalTitle').textContent = title;
            document.getElementById('confirmModalBody').textContent = message;
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            const confirmBtn = document.getElementById('confirmModalBtn');
            const onConfirm = () => { modal.hide(); confirmBtn.removeEventListener('click', onConfirm); resolve(true); };
            const onHidden = () => { confirmBtn.removeEventListener('click', onConfirm); modalEl.removeEventListener('hidden.bs.modal', onHidden); resolve(false); };
            confirmBtn.addEventListener('click', onConfirm);
            modalEl.addEventListener('hidden.bs.modal', onHidden);
        });
    },
    getCategoryBadge(category) {
        const colors = { 文学: 'primary', 科技: 'success', 历史: 'warning', 哲学: 'info', 艺术: 'danger', 教育: 'secondary', 其他: 'dark' };
        return colors[category] || 'primary';
    }
};

// ==================== Vue Application ====================
const app = createApp({
    setup() {
        const currentPage = ref('dashboard');
        const isLoading = ref(true);

        // ===== Dashboard State =====
        const dashboardData = reactive({ bookStats: null, readerStats: null, popularBooks: [], overdueList: [], loading: false });

        // ===== Books State =====
        const booksData = reactive({
            items: [], total: 0, page: 1, pageSize: CONFIG.DEFAULT_PAGE_SIZE,
            keyword: '', category: '', loading: false,
            showForm: false, editingBook: null, submitting: false,
            form: { title: '', author: '', isbn: '', publisher: '', publish_year: null, category: '', description: '', total_stock: 1 }
        });

        // ===== Readers State =====
        const readersData = reactive({
            items: [], total: 0, page: 1, pageSize: CONFIG.DEFAULT_PAGE_SIZE,
            keyword: '', loading: false,
            showForm: false, editingReader: null, submitting: false,
            form: { name: '', id_card: '', phone: '', email: '' }
        });

        // ===== Borrowings State =====
        const borrowingsData = reactive({
            borrowBookId: '', borrowReaderId: '', borrowLoading: false, borrowResult: null,
            returnBorrowingId: '', returnLoading: false, returnResult: null,
            activeReaderId: '', activeBorrowings: [], activeLoading: false
        });

        // ===== Stats State =====
        const statsData = reactive({
            bookStats: null, readerStats: null, popularBooks: [],
            popularLimit: 10, overduePage: 1, overduePageSize: 20,
            overdueItems: [], overdueTotal: 0, loading: false
        });

        // ===== Computed =====
        const booksTotalPages = computed(() => Math.max(1, Math.ceil(booksData.total / booksData.pageSize)));
        const readersTotalPages = computed(() => Math.max(1, Math.ceil(readersData.total / readersData.pageSize)));
        const overdueTotalPages = computed(() => Math.max(1, Math.ceil(statsData.overdueTotal / statsData.overduePageSize)));

        // ===== Navigation =====
        function navigate(page) {
            currentPage.value = page;
            document.querySelectorAll('.navbar .nav-link').forEach(el => {
                el.classList.toggle('active', el.dataset.page === page);
            });
            nextTick(() => {
                switch (page) {
                    case 'dashboard': loadDashboard(); break;
                    case 'books': loadBooks(); break;
                    case 'readers': loadReaders(); break;
                    case 'stats': loadStats(); break;
                }
            });
        }

        // ===== Dashboard =====
        async function loadDashboard() {
            dashboardData.loading = true;
            try {
                const [bookStats, readerStats, popularBooks, overdueData] = await Promise.all([
                    Api.stats.books(), Api.stats.readers(),
                    Api.stats.popularBooks(5), Api.stats.overdueBorrowings({ page: 1, page_size: 5 })
                ]);
                dashboardData.bookStats = bookStats;
                dashboardData.readerStats = readerStats;
                dashboardData.popularBooks = popularBooks;
                dashboardData.overdueList = overdueData?.items || overdueData || [];
            } catch (err) {
                Utils.showToast('加载仪表盘数据失败: ' + err.message, 'error');
            } finally { dashboardData.loading = false; }
        }

        // ===== Books =====
        async function loadBooks() {
            booksData.loading = true;
            try {
                const result = await Api.books.search({
                    keyword: booksData.keyword || undefined,
                    category: booksData.category || undefined,
                    page: booksData.page, page_size: booksData.pageSize
                });
                booksData.items = result.items || [];
                booksData.total = result.total || 0;
            } catch (err) {
                Utils.showToast('加载图书列表失败: ' + err.message, 'error');
                booksData.items = []; booksData.total = 0;
            } finally { booksData.loading = false; }
        }
        function searchBooks() { booksData.page = 1; loadBooks(); }
        function resetBookSearch() { booksData.keyword = ''; booksData.category = ''; booksData.page = 1; loadBooks(); }
        function openBookForm(book = null) {
            booksData.editingBook = book;
            booksData.form = book ? {
                title: book.title, author: book.author, isbn: book.isbn,
                publisher: book.publisher || '', publish_year: book.publish_year,
                category: book.category || '', description: book.description || '',
                total_stock: book.total_stock
            } : { title: '', author: '', isbn: '', publisher: '', publish_year: null, category: '', description: '', total_stock: 1 };
            booksData.showForm = true;
        }
        function closeBookForm() { booksData.showForm = false; booksData.editingBook = null; }
        async function submitBookForm() {
            booksData.submitting = true;
            try {
                const form = {};
                for (const [k, v] of Object.entries(booksData.form)) {
                    if (v !== '' && v !== null && v !== undefined) form[k] = v;
                }
                if (form.total_stock) form.total_stock = Number(form.total_stock);
                if (form.publish_year) form.publish_year = Number(form.publish_year);
                if (booksData.editingBook) {
                    await Api.books.update(booksData.editingBook.id, form);
                    Utils.showToast('图书信息已更新');
                } else {
                    await Api.books.create(form);
                    Utils.showToast('图书已添加');
                }
                closeBookForm();
                loadBooks();
            } catch (err) { Utils.showToast('保存失败: ' + err.message, 'error'); }
            finally { booksData.submitting = false; }
        }
        async function deactivateBook(book) {
            if (!await Utils.showConfirm('确认下架', `确定要将《${book.title}》下架吗？`)) return;
            try { await Api.books.deactivate(book.id); Utils.showToast('图书已下架'); loadBooks(); }
            catch (err) { Utils.showToast('操作失败: ' + err.message, 'error'); }
        }
        async function activateBook(book) {
            try { await Api.books.activate(book.id); Utils.showToast('图书已上架'); loadBooks(); }
            catch (err) { Utils.showToast('操作失败: ' + err.message, 'error'); }
        }

        // ===== Readers =====
        async function loadReaders() {
            readersData.loading = true;
            try {
                const result = await Api.readers.search({
                    keyword: readersData.keyword || undefined,
                    page: readersData.page, page_size: readersData.pageSize
                });
                readersData.items = result.items || [];
                readersData.total = result.total || 0;
            } catch (err) {
                Utils.showToast('加载读者列表失败: ' + err.message, 'error');
                readersData.items = []; readersData.total = 0;
            } finally { readersData.loading = false; }
        }
        function searchReaders() { readersData.page = 1; loadReaders(); }
        function resetReaderSearch() { readersData.keyword = ''; readersData.page = 1; loadReaders(); }
        function openReaderForm(reader = null) {
            readersData.editingReader = reader;
            readersData.form = reader ? {
                name: reader.name, id_card: reader.id_card,
                phone: reader.phone || '', email: reader.email || ''
            } : { name: '', id_card: '', phone: '', email: '' };
            readersData.showForm = true;
        }
        function closeReaderForm() { readersData.showForm = false; readersData.editingReader = null; }
        async function submitReaderForm() {
            readersData.submitting = true;
            try {
                const form = {};
                for (const [k, v] of Object.entries(readersData.form)) { if (v !== '' && v !== null) form[k] = v; }
                if (readersData.editingReader) {
                    await Api.readers.update(readersData.editingReader.id, form);
                    Utils.showToast('读者信息已更新');
                } else {
                    await Api.readers.create(form);
                    Utils.showToast('读者已注册');
                }
                closeReaderForm();
                loadReaders();
            } catch (err) { Utils.showToast('保存失败: ' + err.message, 'error'); }
            finally { readersData.submitting = false; }
        }
        async function toggleReaderStatus(reader) {
            const action = reader.is_active ? '冻结' : '解冻';
            if (!await Utils.showConfirm(`确认${action}`, `确定要${action}读者「${reader.name}」吗？`)) return;
            try { await Api.readers.update(reader.id, { is_active: !reader.is_active }); Utils.showToast(`读者已${action}`); loadReaders(); }
            catch (err) { Utils.showToast('操作失败: ' + err.message, 'error'); }
        }

        // ===== Borrowings =====
        async function borrowBook() {
            const bookId = Number(borrowingsData.borrowBookId);
            const readerId = Number(borrowingsData.borrowReaderId);
            if (!bookId || !readerId) { Utils.showToast('请填写图书ID和读者ID', 'warning'); return; }
            borrowingsData.borrowLoading = true;
            borrowingsData.borrowResult = null;
            try {
                borrowingsData.borrowResult = await Api.borrowings.borrow({ book_id: bookId, reader_id: readerId });
                Utils.showToast('借书成功！');
                borrowingsData.borrowBookId = '';
                borrowingsData.borrowReaderId = '';
            } catch (err) { Utils.showToast('借书失败: ' + err.message, 'error'); }
            finally { borrowingsData.borrowLoading = false; }
        }
        async function returnBook() {
            const borrowingId = Number(borrowingsData.returnBorrowingId);
            if (!borrowingId) { Utils.showToast('请填写借阅记录ID', 'warning'); return; }
            borrowingsData.returnLoading = true;
            borrowingsData.returnResult = null;
            try {
                borrowingsData.returnResult = await Api.borrowings.returnBook({ borrowing_id: borrowingId });
                Utils.showToast('还书成功！');
                borrowingsData.returnBorrowingId = '';
                if (borrowingsData.activeReaderId) loadReaderActiveBorrowings();
            } catch (err) { Utils.showToast('还书失败: ' + err.message, 'error'); }
            finally { borrowingsData.returnLoading = false; }
        }
        async function loadReaderActiveBorrowings() {
            const readerId = Number(borrowingsData.activeReaderId);
            if (!readerId) { borrowingsData.activeBorrowings = []; return; }
            borrowingsData.activeLoading = true;
            try { borrowingsData.activeBorrowings = await Api.borrowings.getReaderActiveBorrowings(readerId) || []; }
            catch (err) { Utils.showToast('查询读者借阅记录失败: ' + err.message, 'error'); borrowingsData.activeBorrowings = []; }
            finally { borrowingsData.activeLoading = false; }
        }

        // ===== Statistics =====
        async function loadStats() {
            statsData.loading = true;
            try {
                const [bookStats, readerStats, popularBooks] = await Promise.all([
                    Api.stats.books(), Api.stats.readers(), Api.stats.popularBooks(statsData.popularLimit)
                ]);
                statsData.bookStats = bookStats;
                statsData.readerStats = readerStats;
                statsData.popularBooks = popularBooks;
                await loadOverdueList();
            } catch (err) { Utils.showToast('加载统计数据失败: ' + err.message, 'error'); }
            finally { statsData.loading = false; }
        }
        async function loadOverdueList() {
            try {
                const result = await Api.stats.overdueBorrowings({ page: statsData.overduePage, page_size: statsData.overduePageSize });
                statsData.overdueItems = result?.items || result || [];
                statsData.overdueTotal = result?.total || statsData.overdueItems.length;
            } catch (err) { Utils.showToast('加载逾期清单失败: ' + err.message, 'error'); }
        }

        // ===== Initialization =====
        onMounted(async () => {
            document.getElementById('loading-indicator').style.display = 'none';
            document.getElementById('page-content').style.display = 'block';
            isLoading.value = false;
            // Set default active nav
            document.querySelector('.navbar .nav-link[data-page="dashboard"]')?.classList.add('active');
            await loadDashboard();
        });

        // ===== Template =====
        return {
            // Utils exposed to template
            Utils,
            // Navigation
            currentPage, navigate,
            // Dashboard
            dashboardData,
            // Books
            booksData, booksTotalPages,
            loadBooks, searchBooks, resetBookSearch,
            openBookForm, closeBookForm, submitBookForm,
            deactivateBook, activateBook,
            // Readers
            readersData, readersTotalPages,
            loadReaders, searchReaders, resetReaderSearch,
            openReaderForm, closeReaderForm, submitReaderForm,
            toggleReaderStatus,
            // Borrowings
            borrowingsData,
            borrowBook, returnBook, loadReaderActiveBorrowings,
            // Stats
            statsData, overdueTotalPages,
            loadStats, loadOverdueList,
        };
    },
    template: `
        <div class="page-section">
            <!-- ==================== DASHBOARD ==================== -->
            <div v-if="currentPage === 'dashboard'">
                <h3 class="page-title"><i class="bi bi-speedometer2"></i>系统仪表盘</h3>
                <div v-if="dashboardData.loading" class="text-center py-4">
                    <div class="spinner-border text-primary"><span class="visually-hidden">加载中...</span></div>
                </div>
                <div v-else>
                    <!-- Stats Cards -->
                    <div class="row g-3 mb-4">
                        <div class="col-md-3">
                            <div class="stat-card" style="background: linear-gradient(135deg, #4a6cf7, #6c8aff);">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <div class="stat-number">{{ dashboardData.bookStats?.total_books || 0 }}</div>
                                        <div class="stat-label">图书总数</div>
                                    </div>
                                    <i class="bi bi-book-fill stat-icon"></i>
                                </div>
                            </div>
                        </div>
                       