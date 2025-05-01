<script setup>
import { ref, onMounted } from 'vue';
import { adminService } from '../../services/api';
import { formatDate } from '../../utils/formatters';

// State
const users = ref([]);
const loading = ref(true);
const error = ref('');
const success = ref('');
const searchQuery = ref('');
const roleFilter = ref('');
const statusFilter = ref('');
const pagination = ref({
  page: 1,
  per_page: 10,
  total_pages: 1,
  total_items: 0
});

// Computed functions
const getStatusBadgeClass = (user) => {
  if (!user.is_active) return 'bg-danger';
  
  if (user.role === 'sponsor') {
    if (user.sponsor_approved === true) return 'bg-success';
    if (user.sponsor_approved === false) return 'bg-danger';
    return 'bg-warning';
  }
  
  if (user.role === 'influencer') {
    if (user.influencer_approved === true) return 'bg-success';
    if (user.influencer_approved === false) return 'bg-danger';
    return 'bg-warning';
  }
  
  return 'bg-secondary';
};

const getStatusText = (user) => {
  if (!user.is_active) return 'Inactive';
  
  if (user.role === 'sponsor') {
    if (user.sponsor_approved === true) return 'Approved';
    if (user.sponsor_approved === false) return 'Rejected';
    return 'Pending Approval';
  }
  
  if (user.role === 'influencer') {
    if (user.influencer_approved === true) return 'Approved';
    if (user.influencer_approved === false) return 'Rejected';
    return 'Pending Approval';
  }
  
  return 'Active';
};

// Methods
const loadUsers = async (page = 1) => {
  try {
    loading.value = true;
    error.value = '';
    
    const params = {
      page,
      per_page: pagination.value.per_page,
      query: searchQuery.value,
      role: roleFilter.value,
      status: statusFilter.value
    };
    
    // Remove empty params
    Object.keys(params).forEach(key => {
      if (params[key] === '') {
        delete params[key];
      }
    });
    
    const response = await adminService.getUsers(params);
    users.value = response.data.users;
    pagination.value = response.data.pagination;
  } catch (err) {
    console.error('Error loading users:', err);
    error.value = 'Failed to load users. Please try again.';
  } finally {
    loading.value = false;
  }
};

const viewUser = (user) => {
  // Placeholder for view user functionality
  console.log('Viewing user:', user);
  // This would typically open a modal or navigate to a user detail page
};

const flagUser = async (userId) => {
  if (!confirm('Are you sure you want to flag this user? They will not be able to log in and their content will be restricted.')) {
    return;
  }
  
  try {
    loading.value = true;
    await adminService.flagUser(userId);
    success.value = 'User has been flagged';
    await loadUsers(pagination.value.page); // Refresh the current page
  } catch (err) {
    console.error('Error flagging user:', err);
    error.value = 'Failed to flag user. Please try again.';
  } finally {
    loading.value = false;
  }
};

const unflagUser = async (userId) => {
  if (!confirm('Are you sure you want to unflag this user? This will restore their ability to log in and interact with the platform.')) {
    return;
  }
  
  try {
    loading.value = true;
    await adminService.unflagUser(userId);
    success.value = 'User has been unflagged';
    await loadUsers(pagination.value.page); // Refresh the current page
  } catch (err) {
    console.error('Error unflagging user:', err);
    error.value = 'Failed to unflag user. Please try again.';
  } finally {
    loading.value = false;
  }
};

const activateUser = async (userId) => {
  try {
    loading.value = true;
    await adminService.activateUser(userId);
    success.value = 'User has been activated';
    await loadUsers(pagination.value.page);
  } catch (err) {
    console.error('Error activating user:', err);
    error.value = 'Failed to activate user. Please try again.';
  } finally {
    loading.value = false;
  }
};

const deactivateUser = async (userId) => {
  if (!confirm('Are you sure you want to deactivate this user? They will not be able to access their account.')) {
    return;
  }
  
  try {
    loading.value = true;
    await adminService.deactivateUser(userId);
    success.value = 'User has been deactivated';
    await loadUsers(pagination.value.page);
  } catch (err) {
    console.error('Error deactivating user:', err);
    error.value = 'Failed to deactivate user. Please try again.';
  } finally {
    loading.value = false;
  }
};

const applyFilters = () => {
  loadUsers(1); // Reset to page 1 when filters change
};

const clearFilters = () => {
  searchQuery.value = '';
  roleFilter.value = '';
  statusFilter.value = '';
  loadUsers(1);
};

// Initialize
onMounted(() => {
  loadUsers();
});
</script>

<template>
  <div class="admin-users-view py-5">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Manage Users</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <router-link to="/admin/dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item active">Users</li>
          </ol>
        </nav>
      </div>
      
      <!-- Alerts -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <div v-if="success" class="alert alert-success alert-dismissible fade show" role="alert">
        {{ success }}
        <button type="button" class="btn-close" @click="success = ''"></button>
      </div>
      
      <!-- Filters -->
      <div class="card mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">
            <i class="bi bi-funnel me-2"></i>Filter Users
          </h5>
          
          <div class="row g-3">
            <div class="col-md-4">
              <label for="search" class="form-label">Search</label>
              <div class="input-group">
                <span class="input-group-text">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  type="text" 
                  class="form-control" 
                  id="search" 
                  v-model="searchQuery"
                  placeholder="Username, email, ID..."
                >
              </div>
            </div>
            
            <div class="col-md-4">
              <label for="role" class="form-label">Role</label>
              <select class="form-select" id="role" v-model="roleFilter">
                <option value="">All Roles</option>
                <option value="sponsor">Sponsor</option>
                <option value="influencer">Influencer</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            
            <div class="col-md-4">
              <label for="status" class="form-label">Status</label>
              <select class="form-select" id="status" v-model="statusFilter">
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="pending">Pending Approval</option>
                <option value="flagged">Flagged</option>
              </select>
            </div>
          </div>
          
          <div class="d-flex justify-content-end mt-3 gap-2">
            <button class="btn btn-outline-secondary" @click="clearFilters">
              <i class="bi bi-x-circle me-2"></i>Clear Filters
            </button>
            <button class="btn btn-primary" @click="applyFilters">
              <i class="bi bi-search me-2"></i>Search
            </button>
          </div>
        </div>
      </div>
      
      <!-- Users List -->
      <div class="card border-0 shadow-sm overflow-hidden">
        <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
          <h5 class="mb-0">Users List <span class="text-muted fs-6">({{ pagination.total_items || 0 }} total)</span></h5>
          
          <div class="btn-group">
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadUsers(pagination.page - 1)"
              :disabled="pagination.page === 1 || loading"
            >
              <i class="bi bi-chevron-left"></i>
            </button>
            <button class="btn btn-outline-secondary btn-sm" disabled>
              Page {{ pagination.page }} of {{ pagination.total_pages }}
            </button>
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadUsers(pagination.page + 1)"
              :disabled="pagination.page >= pagination.total_pages || loading"
            >
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>
        
        <div class="card-body p-0">
          <!-- Loading State -->
          <div v-if="loading && !users.length" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading users...</p>
          </div>
          
          <!-- Empty State -->
          <div v-else-if="!users.length" class="p-4 text-center">
            <p class="mb-0">No users found matching your filters.</p>
          </div>
          
          <!-- Users Table -->
          <div v-else class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id" :class="{ 'table-danger': user.is_flagged }">
                  <td>
                    <div class="d-flex align-items-center gap-2">
                      <span class="avatar bg-light rounded-circle">
                        <i class="bi bi-person-fill"></i>
                      </span>
                      <div>
                        <div class="fw-semibold">{{ user.username }}</div>
                        <small class="text-muted">ID: {{ user.id }}</small>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div>{{ user.email }}</div>
                  </td>
                  <td>
                    <span class="text-capitalize">{{ user.role }}</span>
                    <span v-if="user.is_flagged" 
                          class="badge bg-danger ms-2" 
                          title="This user cannot log in and their content is restricted">
                      FLAGGED
                    </span>
                  </td>
                  <td>
                    <span 
                      class="badge" 
                      :class="getStatusBadgeClass(user)"
                    >
                      {{ getStatusText(user) }}
                    </span>
                  </td>
                  <td>{{ formatDate(user.created_at) }}</td>
                  <td>
                    <div class="dropdown">
                      <button class="btn btn-sm btn-light border" type="button" data-bs-toggle="dropdown">
                        <i class="bi bi-three-dots-vertical"></i>
                      </button>
                      <ul class="dropdown-menu">
                        <!-- View and edit actions -->
                        <li>
                          <button class="dropdown-item" @click="viewUser(user)">
                            <i class="bi bi-eye text-primary me-2"></i>View Details
                          </button>
                        </li>
                        
                        <!-- Flag/Unflag actions -->
                        <li v-if="!user.is_flagged">
                          <button class="dropdown-item" @click="flagUser(user.id)">
                            <i class="bi bi-flag-fill text-danger me-2"></i>Flag User
                          </button>
                        </li>
                        <li v-else>
                          <button class="dropdown-item" @click="unflagUser(user.id)">
                            <i class="bi bi-flag text-success me-2"></i>Unflag User
                          </button>
                        </li>
                        
                        <!-- Active/Inactive toggle -->
                        <li v-if="user.is_active">
                          <button class="dropdown-item" @click="deactivateUser(user.id)">
                            <i class="bi bi-x-circle text-warning me-2"></i>Deactivate
                          </button>
                        </li>
                        <li v-else>
                          <button class="dropdown-item" @click="activateUser(user.id)">
                            <i class="bi bi-check-circle text-success me-2"></i>Activate
                          </button>
                        </li>
                      </ul>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 