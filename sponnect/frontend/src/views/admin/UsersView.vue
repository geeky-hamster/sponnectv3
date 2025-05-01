<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { adminService } from '../../services/api'
import debounce from 'lodash/debounce'
import * as bootstrap from 'bootstrap'

const users = ref([])
const filteredUsers = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')

// Add pagination tracking
const pagination = ref({
  page: 1,
  per_page: 20,
  total_pages: 1,
  total_items: 0
})

// For profile modal
const selectedUser = ref(null)
const showProfileModal = ref(false)
const bootstrapModalInstance = ref(null)
const modalElement = ref(null)

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

const loadUsers = async (page = 1) => {
  try {
    loading.value = true
    error.value = ''
    
    // Add pagination and filter parameters
    const params = {
      page,
      per_page: pagination.value.per_page
    }
    
    // Add filter parameters if they exist
    if (filters.search) params.search = filters.search
    if (filters.role) params.role = filters.role
    if (filters.status) {
      // Map frontend status filter to backend status parameter
      if (filters.status === 'flagged') {
        params.flagged = 'true'
      } else {
        params.status = filters.status
      }
    }
    
    const response = await adminService.getUsers(params)
    console.log('Response from getUsers:', response.data)
    users.value = response.data.users || []
    
    // Update pagination data
    if (response.data.pagination) {
      pagination.value = response.data.pagination
    }
    
    // Ensure approval fields are correctly set
    users.value = users.value.map(user => {
      // Make sure sponsor_approved and influencer_approved are boolean values
      if (user.role === 'sponsor') {
        user.sponsor_approved = user.sponsor_approved === true
      } else if (user.role === 'influencer') {
        user.influencer_approved = user.influencer_approved === true
      }
      return user
    })
    
    console.log('Processed user data:', users.value.map(user => ({
      id: user.id,
      username: user.username,
      role: user.role,
      sponsor_approved: user.sponsor_approved,
      influencer_approved: user.influencer_approved
    })))
    
    applyFilters()
  } catch (err) {
    console.error('Error loading users:', err)
    error.value = 'Failed to load users. Please try again.'
  } finally {
    loading.value = false
  }
}

// Apply filters to users list
const applyFilters = () => {
  // Since we're now sending filters to the API, we don't need local filtering
  // Just set filteredUsers to the users received from the API
  filteredUsers.value = users.value;
  
  // Debug log - filtered results
  console.log('Filtered users:', filteredUsers.value.length);
}

// Watch for filter changes and apply them
const debouncedSearch = debounce(() => {
  loadUsers(1); // Reset to page 1 when filters change
}, 300);

watch(filters, () => {
  debouncedSearch();
}, { deep: true });

// Clear all filters
const clearFilters = () => {
  filters.search = '';
  filters.role = '';
  filters.status = '';
  loadUsers(1); // Reset to page 1 and reload
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return "N/A"
  
  try {
    const date = new Date(dateString)
    
    // Use explicit formatting to avoid locale differences
    const day = date.getDate().toString().padStart(2, "0")
    const month = (date.getMonth() + 1).toString().padStart(2, "0") // Months are 0-indexed
    const year = date.getFullYear()
    
    // Format as DD-MM-YYYY
    return `${day}-${month}-${year}`
  } catch (e) {
    console.error("Error formatting date:", e)
    return "Invalid date"
  }
}

// Validate email format
const isValidEmail = (email) => {
  if (!email) return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Show user profile in modal
const viewUserProfile = (user) => {
  try {
    // First set the user and enable the modal in the DOM
    selectedUser.value = user
    showProfileModal.value = true
    
    // Need to wait for Vue to render the modal in the DOM
    setTimeout(() => {
      try {
        // Clean up any existing modal instances and backdrops first
        cleanupModal(false) // false = don't toggle showProfileModal
        
        // Now the modal element should be available
        if (modalElement.value) {
          // Create new modal instance
          bootstrapModalInstance.value = new bootstrap.Modal(modalElement.value)
          bootstrapModalInstance.value.show()
        } else {
          console.error('Modal element not found in DOM')
        }
      } catch (err) {
        console.error('Error initializing modal:', err)
      }
    }, 100) // Increase the timeout to ensure DOM is updated
  } catch (err) {
    console.error('Error in viewUserProfile:', err)
  }
}

// Close the modal and clean up properly
const closeModal = () => {
  try {
    if (bootstrapModalInstance.value) {
      bootstrapModalInstance.value.hide()
    }
    cleanupModal()
  } catch (err) {
    console.error('Error closing modal:', err)
    // Force cleanup in case of error
    cleanupModal(true)
  }
}

// Function to clean up modal resources
const cleanupModal = (toggleModal = true) => {
  try {
    if (toggleModal) {
      showProfileModal.value = false
    }
    
    // Dispose the modal instance
    if (bootstrapModalInstance.value) {
      bootstrapModalInstance.value.dispose()
      bootstrapModalInstance.value = null
    }
    
    // Clean up manually in case bootstrap doesn't
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.remove()
    })
    
    // Make sure body doesn't have modal classes
    document.body.classList.remove('modal-open')
    document.body.style.overflow = ''
    document.body.style.paddingRight = ''
  } catch (err) {
    console.error('Error cleaning up modal:', err)
    // Last resort cleanup
    showProfileModal.value = false
    bootstrapModalInstance.value = null
  }
}

// Flag/unflag user
const toggleFlagUser = async (user) => {
  try {
    actionLoading.value = true
    
    if (user.is_flagged) {
      await unflagUser(user.id)
    } else {
      await adminService.flagUser(user.id)
      success.value = 'User has been flagged'
      // Reload the current page
      await loadUsers(pagination.value.page)
    }
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error toggling user flag status:', err)
    error.value = 'Failed to update flag status. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Approve user (works for both sponsors and influencers)
const approveUser = async (user) => {
  try {
    // Only allow approving pending users
    if ((user.role === 'sponsor' && user.sponsor_approved === true) || 
        (user.role === 'influencer' && user.influencer_approved === true)) {
      error.value = `This ${user.role} is already approved`;
      return;
    }
    
    actionLoading.value = true
    
    if (user.role === 'sponsor') {
      await adminService.approveSponsor(user.id)
      success.value = 'Sponsor approved successfully'
      // Update the user's approval status in the list
      const index = users.value.findIndex(u => u.id === user.id)
      if (index !== -1) {
        users.value[index].sponsor_approved = true
      }
      
      // Update the selected user if viewing in modal
      if (selectedUser.value && selectedUser.value.id === user.id) {
        selectedUser.value.sponsor_approved = true
      }
    } else if (user.role === 'influencer') {
      await adminService.approveInfluencer(user.id)
      success.value = 'Influencer approved successfully'
      // Update the user's approval status in the list
      const index = users.value.findIndex(u => u.id === user.id)
      if (index !== -1) {
        users.value[index].influencer_approved = true
      }
      
      // Update the selected user if viewing in modal
      if (selectedUser.value && selectedUser.value.id === user.id) {
        selectedUser.value.influencer_approved = true
      }
    }
    
    // Reload with current page
    await loadUsers(pagination.value.page)
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error(`Error approving ${user.role}:`, err)
    error.value = 'Failed to update approval status. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Reject user (works for both sponsors and influencers)
const rejectUser = async (user) => {
  try {
    if ((user.role === 'sponsor' && user.sponsor_approved === true) ||
        (user.role === 'influencer' && user.influencer_approved === true)) {
      error.value = `Cannot reject an already approved ${user.role}`;
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
    
    // Close the modal since we're removing the user from the list
    if (selectedUser.value && selectedUser.value.id === user.id) {
      closeModal()
    }
    
    // Reload with current page
    await loadUsers(pagination.value.page)
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error(`Error rejecting ${user.role}:`, err)
    error.value = 'Failed to reject user. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Activate user function
const activateUser = async (user) => {
  try {
    if (user.is_active) {
      error.value = 'User is already active';
      return;
    }
    
    actionLoading.value = true
    
    await adminService.activateUser(user.id)
    success.value = 'User activated successfully'
    
    // Update the user's active status
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].is_active = true
      
      // Update the selected user if viewing in modal
      if (selectedUser.value && selectedUser.value.id === user.id) {
        selectedUser.value.is_active = true
      }
    }
    
    // Reload with current page
    await loadUsers(pagination.value.page)
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error activating user:', err)
    error.value = 'Failed to activate user. Please try again.'
  } finally {
    actionLoading.value = false
  }
}

// Deactivate user function
const deactivateUser = async (user) => {
  try {
    if (!user.is_active) {
      error.value = 'User is already inactive';
      return;
    }
    
    actionLoading.value = true
    
    await adminService.deactivateUser(user.id)
    success.value = 'User deactivated successfully'
    
    // Update the user's active status
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].is_active = false
      
      // Update the selected user if viewing in modal
      if (selectedUser.value && selectedUser.value.id === user.id) {
        selectedUser.value.is_active = false
      }
    }
    
    // Reload with current page
    await loadUsers(pagination.value.page)
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    console.error('Error deactivating user:', err)
    error.value = 'Failed to deactivate user. Please try again.'
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
onMounted(() => {
  loadUsers()
})

const unflagUser = async (userId) => {
  // Create a custom confirmation dialog with options
  const confirmed = confirm('Are you sure you want to unflag this user? This will restore their ability to log in and interact with the platform.');
  
  if (!confirmed) {
    return;
  }
  
  // Ask if the admin wants to cascade unflag
  const cascadeUnflag = confirm('Do you also want to unflag all associated content (campaigns and ad requests)?\n\nClick OK to unflag everything.\nClick Cancel to unflag only the user.');
  
  try {
    loading.value = true;
    const response = await adminService.unflagUser(userId, cascadeUnflag);
    
    // Create a more detailed success message based on what was unflagged
    let successMessage = 'User has been unflagged';
    
    if (cascadeUnflag && response.data.unflagged_items) {
      const items = response.data.unflagged_items;
      successMessage += ` along with ${items.campaigns || 0} campaigns and ${items.ad_requests || 0} ad requests`;
    }
    
    success.value = successMessage;
    // Reload the current page
    await loadUsers(pagination.value.page);
  } catch (err) {
    console.error('Error unflagging user:', err);
    error.value = 'Failed to unflag user. Please try again.';
  } finally {
    loading.value = false;
  }
};
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
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
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
          <h5 class="mb-0">Users List <span class="text-muted fs-6">({{ filteredUsers.length }} of {{ pagination.total_items || 0 }} users)</span></h5>
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
                    'badge bg-success': user.is_active && ((user.role === 'sponsor' && user.sponsor_approved === true) || 
                               (user.role === 'influencer' && user.influencer_approved === true) || 
                               user.role === 'admin'),
                    'badge bg-warning': (user.role === 'sponsor' && user.sponsor_approved === false) || 
                               (user.role === 'influencer' && user.influencer_approved === false),
                    'badge bg-secondary': !user.is_active
                  }">
                    {{ 
                      !user.is_active ? 'Inactive' : 
                      ((user.role === 'sponsor' && user.sponsor_approved === false) || 
                       (user.role === 'influencer' && user.influencer_approved === false)) ? 'Pending Approval' : 
                      'Active' 
                    }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td class="text-center">
                  <button class="btn btn-primary btn-sm" @click="viewUserProfile(user)" title="View Profile">
                    <i class="bi bi-eye-fill"></i> View
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Pagination controls -->
        <div class="card-footer bg-white py-3 d-flex justify-content-between align-items-center">
          <span class="text-muted">
            Showing {{ filteredUsers.length }} of {{ pagination.total_items || 0 }} users
          </span>
          <div class="btn-group">
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadUsers(pagination.page - 1)"
              :disabled="pagination.page <= 1 || loading"
            >
              <i class="bi bi-chevron-left"></i> Previous
            </button>
            <button class="btn btn-outline-secondary btn-sm" disabled>
              Page {{ pagination.page }} of {{ pagination.total_pages }}
            </button>
            <button 
              class="btn btn-outline-secondary btn-sm" 
              @click="loadUsers(pagination.page + 1)"
              :disabled="pagination.page >= pagination.total_pages || loading"
            >
              Next <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>
      </div>
      
      <!-- User Profile Modal - Using v-if with showProfileModal to completely remove from DOM when closed -->
      <div ref="modalElement" class="modal fade" id="userProfileModal" tabindex="-1" aria-labelledby="userProfileModalLabel" 
           v-if="showProfileModal">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header bg-light">
              <h5 class="modal-title fw-bold" id="userProfileModalLabel">
                <i class="bi bi-person-badge me-2"></i>User Profile
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" @click="closeModal"></button>
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
                  <span class="d-block mt-2" :class="{
                    'badge bg-success': selectedUser.is_active && ((selectedUser.role === 'sponsor' && selectedUser.sponsor_approved === true) || 
                                       (selectedUser.role === 'influencer' && selectedUser.influencer_approved === true) || 
                                       selectedUser.role === 'admin'),
                    'badge bg-warning': (selectedUser.role === 'sponsor' && selectedUser.sponsor_approved === false) || 
                                       (selectedUser.role === 'influencer' && selectedUser.influencer_approved === false),
                    'badge bg-secondary': !selectedUser.is_active
                  }">
                    {{ 
                      !selectedUser.is_active ? 'Inactive' : 
                      ((selectedUser.role === 'sponsor' && selectedUser.sponsor_approved === false) || 
                       (selectedUser.role === 'influencer' && selectedUser.influencer_approved === false)) ? 'Pending Approval' : 
                      'Active' 
                    }}
                  </span>
                  <div v-if="selectedUser.is_flagged" class="badge bg-danger mt-2">
                    <i class="bi bi-flag-fill me-1"></i> Flagged
                  </div>
                  <p class="text-muted mt-3">Joined on {{ formatDate(selectedUser.created_at) }}</p>
                </div>
                <div class="col-md-8">
                  <div class="mb-4">
                    <h6 class="fw-bold border-bottom pb-2">Account Information</h6>
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
                          <tr v-if="selectedUser.role === 'sponsor'">
                            <th scope="row">Company</th>
                            <td>{{ selectedUser.company_name || 'Not provided' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'sponsor'">
                            <th scope="row">Industry</th>
                            <td>{{ selectedUser.industry || 'Not provided' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Display Name</th>
                            <td>{{ selectedUser.influencer_name || 'Not specified' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Category</th>
                            <td>{{ selectedUser.category || 'Not specified' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Niche</th>
                            <td>{{ selectedUser.niche || 'Not specified' }}</td>
                          </tr>
                          <tr v-if="selectedUser.role === 'influencer'">
                            <th scope="row">Reach</th>
                            <td>{{ selectedUser.reach ? selectedUser.reach.toLocaleString('en-IN', ) : 'Not specified' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  <div>
                    <h6 class="fw-bold border-bottom pb-2">Actions</h6>
                    <div class="d-flex gap-2 flex-wrap">
                      <!-- For pending users: show approve and reject buttons -->
                      <div v-if="(selectedUser.role === 'sponsor' && selectedUser.sponsor_approved === false) || 
                                  (selectedUser.role === 'influencer' && selectedUser.influencer_approved === false)" 
                               class="d-flex gap-2 flex-wrap">
                        <button 
                          class="btn btn-success"
                          @click="approveUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-check-circle me-1"></i>
                          Approve {{ selectedUser.role === 'sponsor' ? 'Sponsor' : 'Influencer' }}
                        </button>
                        
                        <button 
                          class="btn btn-danger"
                          @click="rejectUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-x-circle me-1"></i>
                          Reject {{ selectedUser.role === 'sponsor' ? 'Sponsor' : 'Influencer' }}
                        </button>
                      </div>
                      
                      <!-- For approved users: show flag/unflag buttons -->
                      <div v-else class="d-flex gap-2 flex-wrap">
                        <button 
                          class="btn" 
                          :class="selectedUser.is_flagged ? 'btn-warning' : 'btn-outline-danger'"
                          @click="toggleFlagUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi" :class="selectedUser.is_flagged ? 'bi-flag me-1' : 'bi-flag-fill me-1'"></i>
                          {{ selectedUser.is_flagged ? 'Unflag User' : 'Flag User' }}
                        </button>
                        
                        <!-- Additional action buttons for approved users could be added here -->
                        <button 
                          v-if="selectedUser.is_active"
                          class="btn btn-outline-secondary"
                          @click="deactivateUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-person-dash me-1"></i>
                          Deactivate User
                        </button>
                        
                        <button 
                          v-else
                          class="btn btn-outline-success"
                          @click="activateUser(selectedUser)"
                          :disabled="actionLoading"
                        >
                          <i class="bi bi-person-check me-1"></i>
                          Activate User
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer bg-light">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" @click="closeModal">Close</button>
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
