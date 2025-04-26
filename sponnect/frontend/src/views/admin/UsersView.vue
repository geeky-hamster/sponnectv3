<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { adminService } from '../../services/api'
import debounce from 'lodash/debounce'
import { Modal as bootstrap } from 'bootstrap'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import ProfileIcon from '@/components/common/ProfileIcon.vue'
import ButtonWithConfirmation from '@/components/common/ButtonWithConfirmation.vue'
import ThemedButton from '@/components/common/ThemedButton.vue'
import Modal from '@/components/common/Modal.vue'

const users = ref([])
const filteredUsers = ref([])
const loading = ref(true)
const errorMessage = ref('')
const success = ref('')
const totalUsers = ref(0)

// For profile modal
const selectedUser = ref(null)
const showProfileModal = ref(false)

// For actions
const actionLoading = ref(false)

// Filters
const filters = reactive({
  search: '',
  role: '',
  status: ''
})

// Available filter options
const roleOptions = [
  { value: '', label: 'All Roles' },
  { value: 'admin', label: 'Admin' },
  { value: 'sponsor', label: 'Sponsor' },
  { value: 'influencer', label: 'Influencer' }
]

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'pending', label: 'Pending Approval' },
  { value: 'flagged', label: 'Flagged' }
]

const toast = useToast()
const route = useRoute()
const router = useRouter()

const loadUsers = async () => {
  try {
    loading.value = true
    errorMessage.value = ''
    
    const response = await adminService.getUsers({})
    users.value = response.data.users || []
    totalUsers.value = users.value.length
    applyFilters()
  } catch (err) {
    console.error('Error loading users:', err)
    errorMessage.value = 'Failed to load users. Please try again.'
  } finally {
    loading.value = false
  }
}

// Apply filters to users list
const applyFilters = () => {
  filteredUsers.value = users.value.filter(user => {
    // Search filter (case insensitive)
    const searchMatch = !filters.search || 
      user.username?.toLowerCase().includes(filters.search.toLowerCase()) ||
      user.email?.toLowerCase().includes(filters.search.toLowerCase()) ||
      (user.company_name && user.company_name.toLowerCase().includes(filters.search.toLowerCase()));
    
    // Role filter
    const roleMatch = !filters.role || user.role === filters.role;
    
    // Status filter
    let statusMatch = true;
    if (filters.status) {
      switch (filters.status) {
        case 'active':
          statusMatch = user.is_active && 
            ((user.role === 'sponsor' && user.is_approved) || 
             (user.role === 'influencer' && user.is_approved) ||
             (user.role === 'admin'));
          break;
        case 'inactive':
          statusMatch = !user.is_active;
          break;
        case 'pending':
          statusMatch = (user.role === 'sponsor' && !user.is_approved) || 
                        (user.role === 'influencer' && !user.is_approved);
          break;
        case 'flagged':
          statusMatch = user.is_flagged;
          break;
      }
    }
    
    return searchMatch && roleMatch && statusMatch;
  });
}

// Watch for filter changes and apply them
watch(filters, () => {
  applyFilters();
});

// Clear all filters
const clearFilters = () => {
  filters.search = '';
  filters.role = '';
  filters.status = '';
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

// Validate email format
const isValidEmail = (email) => {
  if (!email) return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Show user profile in modal
const viewUserProfile = (user) => {
  selectedUser.value = user
  showProfileModal.value = true
  
  // Update URL with user ID for sharing
  const url = new URL(window.location.href)
  url.searchParams.set('view', user.id)
  window.history.pushState({ userId: user.id }, '', url)
  
  // Use Bootstrap's modal API to show the modal
  setTimeout(() => {
    const modal = new bootstrap(document.getElementById('userProfileModal'))
    modal.show()
  }, 50)
}

// Handle modal close to update URL
const handleModalClose = () => {
  showProfileModal.value = false
  
  // Remove user ID from URL
  const url = new URL(window.location.href)
  url.searchParams.delete('view')
  window.history.pushState({}, '', url)
}

// Flag/unflag user
const toggleFlagUser = async (user) => {
  try {
    actionLoading.value = true
    
    if (user.is_flagged) {
      await adminService.unflagUser(user.id)
      success.value = 'User unflagged successfully'
      // Update the user's flagged status in the list
      const index = users.value.findIndex(u => u.id === user.id)
      if (index !== -1) {
        users.value[index].is_flagged = false
      }
    } else {
      await adminService.flagUser(user.id)
      success.value = 'User flagged successfully'
      // Update the user's flagged status in the list
      const index = users.value.findIndex(u => u.id === user.id)
      if (index !== -1) {
        users.value[index].is_flagged = true
      }
    }
    
    // Apply filters after update
    applyFilters()
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error toggling user flag status:', err)
    errorMessage.value = 'Failed to update flag status. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Approve/unapprove sponsor
const toggleApproveSponsor = async (user) => {
  try {
    // Only allow approving pending sponsors
    if (user.is_approved) {
      errorMessage.value = 'This sponsor is already approved';
      return;
    }
    
    actionLoading.value = true
    
    await adminService.approveSponsor(user.id)
    success.value = 'Sponsor approved successfully'
    // Update the user's approval status in the list
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].is_approved = true
    }
    
    // Apply filters after update
    applyFilters()
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error approving sponsor:', err)
    errorMessage.value = 'Failed to update approval status. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Approve/unapprove user (works for both sponsors and influencers)
const approveUser = async (user) => {
  try {
    // Only allow approving pending users
    if (user.is_approved) {
      errorMessage.value = `This ${user.role} is already approved`;
      return;
    }
    
    actionLoading.value = true
    
    if (user.role === 'sponsor') {
      await adminService.approveSponsor(user.id)
      success.value = 'Sponsor approved successfully'
    } else if (user.role === 'influencer') {
      await adminService.approveInfluencer(user.id)
      success.value = 'Influencer approved successfully'
    }
    
    // Update the user's approval status in the list
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].is_approved = true
    }
    
    // Apply filters after update
    applyFilters()
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error(`Error approving ${user.role}:`, err)
    errorMessage.value = 'Failed to update approval status. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Reject user (works for both sponsors and influencers)
const rejectUser = async (user) => {
  try {
    if (user.is_approved) {
      errorMessage.value = `Cannot reject an already approved ${user.role}`;
      return;
    }
    
    actionLoading.value = true
    
    if (user.role === 'sponsor') {
      await adminService.rejectSponsor(user.id)
      success.value = 'Sponsor rejected successfully'
    } else if (user.role === 'influencer') {
      await adminService.rejectInfluencer(user.id)
      success.value = 'Influencer rejected successfully'
    }
    
    // Remove the user from the list since they are now deactivated
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value.splice(index, 1)
    }
    
    // Apply filters after update
    applyFilters()
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error(`Error rejecting ${user.role}:`, err)
    errorMessage.value = 'Failed to reject user. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Helper function to get badge class for role
const getRoleBadgeClass = (role) => {
  switch (role) {
    case 'sponsor': return 'bg-primary'
    case 'influencer': return 'bg-info'
    case 'admin': return 'bg-danger'
    default: return 'bg-secondary'
  }
}

// Load users when component mounts
onMounted(async () => {
  try {
    loading.value = true
    await loadUsers() // Wait for users to load
    
    // Check URL for user ID to display
    const urlParams = new URLSearchParams(window.location.search)
    const viewUserId = urlParams.get('view')
    
    if (viewUserId) {
      // Find user in the loaded users
      const userToView = users.value.find(u => u.id.toString() === viewUserId)
      if (userToView) {
        // Show user profile if found
        setTimeout(() => viewUserProfile(userToView), 100)
      }
    }
  } catch (error) {
    console.error('Error loading component:', error)
    errorMessage.value = 'Failed to load users. Please try again.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="admin-users py-5">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>User Management</h1>
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb mb-0">
            <li class="breadcrumb-item">
              <router-link to="/admin/dashboard">Dashboard</router-link>
            </li>
            <li class="breadcrumb-item active">Users</li>
          </ol>
        </nav>
      </div>
      
      <!-- Success alert -->
      <div v-if="success" class="alert alert-success alert-dismissible fade show mb-4" role="alert">
        {{ success }}
        <button type="button" class="btn-close" @click="success = ''"></button>
      </div>
      
      <!-- Error alert -->
      <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        {{ errorMessage }}
        <button type="button" class="btn-close" @click="errorMessage = ''"></button>
      </div>
      
      <!-- Filters -->
      <div class="card shadow-sm border-0 mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">
            <i class="bi bi-funnel me-2"></i>Search Users
          </h5>
          <div class="row g-3">
            <div class="col-md-6">
              <div class="input-group mb-3">
                <span class="input-group-text" id="search-addon">
                  <i class="bi bi-search"></i>
                </span>
                <input
                  type="text"
                  class="form-control"
                  placeholder="Search by name, email, or company"
                  v-model="filters.search"
                  aria-label="Search"
                  aria-describedby="search-addon"
                >
              </div>
            </div>
            
            <div class="col-md-3">
              <div class="form-floating">
                <select class="form-select" id="roleFilter" v-model="filters.role">
                  <option v-for="option in roleOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <label for="roleFilter">Role</label>
              </div>
            </div>
            
            <div class="col-md-3">
              <div class="form-floating">
                <select class="form-select" id="statusFilter" v-model="filters.status">
                  <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <label for="statusFilter">Status</label>
              </div>
            </div>
          </div>
          
          <div class="d-flex justify-content-end mt-2">
            <button class="btn btn-outline-secondary" @click="clearFilters">
              <i class="bi bi-x-circle me-2"></i>Clear Filters
            </button>
          </div>
        </div>
      </div>
      
      <!-- Loading indicator -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading users...</p>
      </div>
      
      <!-- Users table -->
      <div v-else class="card shadow-sm border-0">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0">Users List <span class="text-muted fs-6">({{ filteredUsers.length }} users found)</span></h5>
        </div>
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Joined On</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredUsers.length === 0">
                <td colspan="7" class="text-center py-4">
                  <div class="py-3">
                    <i class="bi bi-search fs-3 text-muted"></i>
                    <p class="mb-0 mt-2">No users found matching your filters</p>
                  </div>
                </td>
              </tr>
              <tr v-for="user in filteredUsers" :key="user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>
                  <div class="d-flex align-items-center">
                    {{ user.email }}
                    <span 
                      v-if="!isValidEmail(user.email)" 
                      class="badge bg-warning ms-2" 
                      title="Invalid email format"
                    >
                      <i class="bi bi-exclamation-triangle"></i>
                    </span>
                  </div>
                </td>
                <td>
                  <span :class="`badge ${getRoleBadgeClass(user.role)}`">
                    {{ user.role }}
                  </span>
                  <span v-if="user.is_flagged" class="badge bg-danger ms-1">
                    <i class="bi bi-flag-fill"></i>
                  </span>
                </td>
                <td>
                  <span :class="{
                    'badge bg-success': user.is_active && ((user.role === 'sponsor' && user.is_approved) || (user.role === 'influencer' && user.is_approved) || user.role === 'admin'),
                    'badge bg-warning': (user.role === 'sponsor' || user.role === 'influencer') && !user.is_approved,
                    'badge bg-secondary': !user.is_active
                  }">
                    {{ 
                      !user.is_active ? 'Inactive' : 
                      ((user.role === 'sponsor' || user.role === 'influencer') && !user.is_approved) ? 'Pending Approval' : 
                      'Active' 
                    }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button 
                      class="btn btn-outline-primary" 
                      title="View user details"
                      @click="viewUserProfile(user)"
                    >
                      <i class="bi bi-eye me-1"></i> View
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- User Profile Modal -->
      <div class="modal fade" id="userProfileModal" tabindex="-1" aria-labelledby="userProfileModalLabel" 
           aria-hidden="true" data-bs-backdrop="static">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="userProfileModalLabel">User Profile</h5>
              <button type="button" class="btn-close" @click="handleModalClose" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body" v-if="selectedUser">
              <div class="row">
                <div class="col-md-4 text-center mb-4 mb-md-0">
                  <div class="avatar-container mb-3">
                    <div class="avatar-placeholder rounded-circle bg-light d-flex align-items-center justify-content-center" 
                         style="width: 150px; height: 150px; margin: 0 auto; font-size: 64px;">
                      {{ selectedUser.username ? selectedUser.username.charAt(0).toUpperCase() : 'U' }}
                    </div>
                  </div>
                  <h5>{{ selectedUser.username }}</h5>
                  <span :class="`badge ${getRoleBadgeClass(selectedUser.role)} mb-2`">
                    {{ selectedUser.role }}
                  </span>
                  <div v-if="selectedUser.is_flagged" class="badge bg-danger mb-2">
                    <i class="bi bi-flag-fill me-1"></i> Flagged
                  </div>
                  <p class="text-muted">Joined on {{ formatDate(selectedUser.created_at) }}</p>
                </div>
                <div class="col-md-8">
                  <div class="mb-3">
                    <h6 class="fw-bold">Account Information</h6>
                    <div class="table-responsive">
                      <table class="table">
                        <tbody>
                          <tr>
                            <th scope="row" style="width: 130px;">User ID</th>
                            <td>{{ selectedUser.id }}</td>
                          </tr>
                          <tr>
                            <th scope="row">Email</th>
                            <td>
                              <div class="d-flex align-items-center">
                                {{ selectedUser.email }}
                                <span 
                                  v-if="!isValidEmail(selectedUser.email)" 
                                  class="badge bg-warning ms-2" 
                                  title="Invalid email format"
                                >
                                  <i class="bi bi-exclamation-triangle"></i>
                                </span>
                              </div>
                            </td>
                          </tr>
                          <tr>
                            <th scope="row">Status</th>
                            <td>
                              <span :class="{
                                'badge bg-success': selectedUser.is_active && ((selectedUser.role === 'sponsor' && selectedUser.is_approved) || (selectedUser.role === 'influencer' && selectedUser.is_approved) || selectedUser.role === 'admin'),
                                'badge bg-warning': (selectedUser.role === 'sponsor' || selectedUser.role === 'influencer') && !selectedUser.is_approved,
                                'badge bg-secondary': !selectedUser.is_active
                              }">
                                {{ 
                                  !selectedUser.is_active ? 'Inactive' : 
                                  ((selectedUser.role === 'sponsor' || selectedUser.role === 'influencer') && !selectedUser.is_approved) ? 'Pending Approval' : 
                                  'Active' 
                                }}
                              </span>
                            </td>
                          </tr>
                          <tr v-if="selectedUser.role === 'sponsor'">
                            <th scope="row">Company</th>
                            <td>{{ selectedUser.company_name || 'Not provided' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'sponsor'">
                            <th scope="row">Industry</th>
                            <td>{{ selectedUser.industry || 'Not provided' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Specialty</th>
                            <td>{{ selectedUser.niche || 'Not specified' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Reach</th>
                            <td>{{ selectedUser.reach ? selectedUser.reach.toLocaleString() : 'Not specified' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  <div>
                    <h6 class="fw-bold">Quick Actions</h6>
                    <div class="d-flex gap-2 flex-wrap">
                      <!-- Show approve/reject buttons for pending users -->
                      <div v-if="(selectedUser.role === 'sponsor' || selectedUser.role === 'influencer') && !selectedUser.is_approved" 
                           class="d-flex gap-2 w-100">
                        <button 
                          class="btn btn-success flex-grow-1"
                          @click="approveUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-check-circle me-2"></i>
                          Approve {{ selectedUser.role === 'sponsor' ? 'Sponsor' : 'Influencer' }}
                        </button>
                        
                        <button 
                          class="btn btn-danger flex-grow-1"
                          @click="rejectUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-x-circle me-2"></i>
                          Reject {{ selectedUser.role === 'sponsor' ? 'Sponsor' : 'Influencer' }}
                        </button>
                      </div>
                      
                      <!-- Show flag button for all users -->
                      <button 
                        class="btn" 
                        :class="selectedUser.is_flagged ? 'btn-warning' : 'btn-outline-danger'"
                        @click="toggleFlagUser(selectedUser)"
                        :disabled="actionLoading"
                      >
                        <i class="bi" :class="selectedUser.is_flagged ? 'bi-flag' : 'bi-flag-fill'"></i>
                        {{ selectedUser.is_flagged ? 'Unflag User' : 'Flag User' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" @click="handleModalClose">Close</button>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<style scoped>
.admin-users {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.avatar-placeholder {
  color: var(--bs-primary);
}
</style> 
                  <div v-if="selectedUser.is_flagged" class="badge bg-danger mb-2">
                    <i class="bi bi-flag-fill me-1"></i> Flagged
                  </div>
                  <p class="text-muted">Joined on {{ formatDate(selectedUser.created_at) }}</p>
                </div>
                <div class="col-md-8">
                  <div class="mb-3">
                    <h6 class="fw-bold">Account Information</h6>
                    <div class="table-responsive">
                      <table class="table">
                        <tbody>
                          <tr>
                            <th scope="row" style="width: 130px;">User ID</th>
                            <td>{{ selectedUser.id }}</td>
                          </tr>
                          <tr>
                            <th scope="row">Email</th>
                            <td>
                              <div class="d-flex align-items-center">
                                {{ selectedUser.email }}
                                <span 
                                  v-if="!isValidEmail(selectedUser.email)" 
                                  class="badge bg-warning ms-2" 
                                  title="Invalid email format"
                                >
                                  <i class="bi bi-exclamation-triangle"></i>
                                </span>
                              </div>
                            </td>
                          </tr>
                          <tr>
                            <th scope="row">Status</th>
                            <td>
                              <span :class="{
                                'badge bg-success': selectedUser.is_active && ((selectedUser.role === 'sponsor' && selectedUser.is_approved) || (selectedUser.role === 'influencer' && selectedUser.is_approved) || selectedUser.role === 'admin'),
                                'badge bg-warning': (selectedUser.role === 'sponsor' || selectedUser.role === 'influencer') && !selectedUser.is_approved,
                                'badge bg-secondary': !selectedUser.is_active
                              }">
                                {{ 
                                  !selectedUser.is_active ? 'Inactive' : 
                                  ((selectedUser.role === 'sponsor' || selectedUser.role === 'influencer') && !selectedUser.is_approved) ? 'Pending Approval' : 
                                  'Active' 
                                }}
                              </span>
                            </td>
                          </tr>
                          <tr v-if="selectedUser.role === 'sponsor'">
                            <th scope="row">Company</th>
                            <td>{{ selectedUser.company_name || 'Not provided' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'sponsor'">
                            <th scope="row">Industry</th>
                            <td>{{ selectedUser.industry || 'Not provided' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Specialty</th>
                            <td>{{ selectedUser.niche || 'Not specified' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Reach</th>
                            <td>{{ selectedUser.reach ? selectedUser.reach.toLocaleString() : 'Not specified' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  <div>
                    <h6 class="fw-bold">Quick Actions</h6>
                    <div class="d-flex gap-2 flex-wrap">
                      <!-- Show approve/reject buttons for pending users -->
                      <div v-if="(selectedUser.role === 'sponsor' || selectedUser.role === 'influencer') && !selectedUser.is_approved" 
                           class="d-flex gap-2 w-100">
                        <button 
                          class="btn btn-success flex-grow-1"
                          @click="approveUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-check-circle me-2"></i>
                          Approve {{ selectedUser.role === 'sponsor' ? 'Sponsor' : 'Influencer' }}
                        </button>
                        
                        <button 
                          class="btn btn-danger flex-grow-1"
                          @click="rejectUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-x-circle me-2"></i>
                          Reject {{ selectedUser.role === 'sponsor' ? 'Sponsor' : 'Influencer' }}
                        </button>
                      </div>
                      
                      <!-- Show flag button for all users -->
                      <button 
                        class="btn" 
                        :class="selectedUser.is_flagged ? 'btn-warning' : 'btn-outline-danger'"
                        @click="toggleFlagUser(selectedUser)"
                        :disabled="actionLoading"
                      >
                        <i class="bi" :class="selectedUser.is_flagged ? 'bi-flag' : 'bi-flag-fill'"></i>
                        {{ selectedUser.is_flagged ? 'Unflag User' : 'Flag User' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" @click="handleModalClose">Close</button>
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<style scoped>
.admin-users {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.avatar-placeholder {
  color: var(--bs-primary);
}
</style> 