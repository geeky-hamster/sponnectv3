<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { authService } from '../services/api'
import { required, email } from '../utils/validation'
import ApiError from '../components/ApiError.vue'
import LoadingState from '../components/LoadingState.vue'

const authStore = useAuthStore()
const profile = ref(null)
const loading = ref(true)
const error = ref('')
const success = ref('')
const isEditing = ref(false)

// Form data (will be populated with profile data)
const formData = ref({})

// Form validation errors
const validationErrors = ref({})

// Computed property to determine user role
const userRole = computed(() => authStore.userRole)
const isSponsor = computed(() => userRole.value === 'sponsor')
const isInfluencer = computed(() => userRole.value === 'influencer')

// Default avatar image if profile photo is missing
const defaultAvatar = 'https://via.placeholder.com/150?text=Profile'

// Compute display name based on available data
const displayName = computed(() => {
  if (!profile.value) return '';
  
  if (isInfluencer.value && profile.value.influencer_name) {
    return profile.value.influencer_name;
  }
  
  if (isSponsor.value && profile.value.company_name) {
    return profile.value.company_name;
  }
  
  return profile.value.username || 'User';
})

// Industry options for sponsors
const industryOptions = [
  'Technology',
  'Fashion',
  'Food & Beverage',
  'Health & Wellness',
  'Beauty',
  'Travel',
  'Financial Services',
  'Entertainment',
  'Retail',
  'Automotive',
  'Education',
  'Fitness',
  'Gaming',
  'Home & Decor',
  'Other'
]

// Category options for influencers
const categoryOptions = [
  'Fashion',
  'Beauty',
  'Fitness',
  'Travel',
  'Food',
  'Technology',
  'Gaming',
  'Lifestyle',
  'Business',
  'Education',
  'Entertainment',
  'Health',
  'Parenting',
  'Sports',
  'Other'
]

onMounted(async () => {
  try {
    loading.value = true
    const response = await authService.getProfile()
    profile.value = response.data || response
    
    // Initialize form data with profile info
    formData.value = { ...profile.value }
    
    console.log('Profile data loaded:', profile.value) // Add logging for debugging
  } catch (err) {
    console.error('Error loading profile:', err)
    error.value = 'Failed to load your profile. Please try again.'
  } finally {
    loading.value = false
  }
})

const toggleEdit = () => {
  if (isEditing.value) {
    // Reset form data to original profile
    formData.value = { ...profile.value }
  }
  isEditing.value = !isEditing.value
  error.value = ''
  success.value = ''
}

const validateForm = () => {
  validationErrors.value = {}
  let isValid = true
  
  // Basic validation
  const nameError = required(formData.value.username, 'Username')
  if (nameError) {
    validationErrors.value.username = nameError
    isValid = false
  }
  
  const emailError = email(formData.value.email)
  if (emailError) {
    validationErrors.value.email = emailError
    isValid = false
  }
  
  // Sponsor validation
  if (isSponsor.value) {
    const companyError = required(formData.value.company_name, 'Company name')
    if (companyError) {
      validationErrors.value.company_name = companyError
      isValid = false
    }
    
    const industryError = required(formData.value.industry, 'Industry')
    if (industryError) {
      validationErrors.value.industry = industryError
      isValid = false
    }
  }
  
  // Influencer validation
  if (isInfluencer.value) {
    const influencerNameError = required(formData.value.influencer_name, 'Influencer name')
    if (influencerNameError) {
      validationErrors.value.influencer_name = influencerNameError
      isValid = false
    }
    
    const categoryError = required(formData.value.category, 'Category')
    if (categoryError) {
      validationErrors.value.category = categoryError
      isValid = false
    }
  }
  
  return isValid
}

const saveProfile = async () => {
  if (!validateForm()) {
    error.value = 'Please fix the validation errors before saving.'
    return
  }
  
  try {
    loading.value = true
    error.value = ''
    success.value = ''
    
    const response = await authService.updateProfile(formData.value)
    
    // Handle the response structure correctly
    if (response.data && response.data.profile) {
      profile.value = response.data.profile
    } else if (response.profile) {
      profile.value = response.profile
    } else if (response.data) {
      profile.value = response.data
    }
    
    // Update formData to match the updated profile
    formData.value = { ...profile.value }
    
    success.value = 'Profile updated successfully'
    isEditing.value = false
  } catch (err) {
    console.error('Error updating profile:', err)
    error.value = err.response?.data?.message || 'Failed to update profile. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="profile-page py-5">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-10 col-lg-8">
          <div class="card shadow border-0">
            <div class="card-body p-4 p-md-5">
              <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="mb-0">My Profile</h1>
                <button 
                  v-if="!loading && profile" 
                  class="btn btn-outline-primary" 
                  @click="toggleEdit"
                >
                  <i :class="isEditing ? 'bi bi-x-lg' : 'bi bi-pencil'" class="me-2"></i>
                  {{ isEditing ? 'Cancel' : 'Edit Profile' }}
                </button>
              </div>
              
              <LoadingState v-if="loading" message="Loading your profile..." />
              
              <ApiError :error="error" v-if="error && !isEditing" @dismiss="error = ''" />
              
              <div v-if="success" class="alert alert-success alert-dismissible fade show">
                {{ success }}
                <button type="button" class="btn-close" @click="success = ''"></button>
              </div>
              
              <!-- View Profile Mode -->
              <div v-if="!isEditing && profile" class="profile-details">
                <!-- Profile Header with Avatar -->
                <div class="text-center mb-4">
                  <div class="avatar-container mb-3">
                    <img 
                      :src="profile.avatar_url || defaultAvatar" 
                      :alt="displayName"
                      class="img-fluid rounded-circle profile-avatar"
                    >
                  </div>
                  <h2 class="mb-1">{{ displayName }}</h2>
                  <p class="text-muted">{{ profile.role ? profile.role.charAt(0).toUpperCase() + profile.role.slice(1) : '' }}</p>
                </div>
                
                <div class="row mb-4">
                  <div class="col-md-6">
                    <h5 class="text-muted mb-2">Username</h5>
                    <p class="fs-5">{{ profile.username || 'Not specified' }}</p>
                  </div>
                  <div class="col-md-6">
                    <h5 class="text-muted mb-2">Email</h5>
                    <p class="fs-5">{{ profile.email || 'Not specified' }}</p>
                  </div>
                </div>
                
                <!-- Sponsor-specific fields -->
                <div v-if="isSponsor" class="sponsor-details">
                  <hr>
                  <h4 class="mb-3">Sponsor Information</h4>
                  
                  <div class="row mb-4">
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Company Name</h5>
                      <p class="fs-5">{{ profile.company_name || 'Not specified' }}</p>
                    </div>
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Industry</h5>
                      <p class="fs-5">{{ profile.industry || 'Not specified' }}</p>
                    </div>
                  </div>
                  
                  <div class="row mb-4">
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Status</h5>
                      <div>
                        <span 
                          :class="{
                            'badge rounded-pill bg-success': profile.sponsor_approved === true,
                            'badge rounded-pill bg-warning': profile.sponsor_approved === null,
                            'badge rounded-pill bg-danger': profile.sponsor_approved === false
                          }"
                        >
                          {{ profile.sponsor_approved === true ? 'Approved' : 
                             profile.sponsor_approved === null ? 'Pending Approval' : 'Rejected' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Influencer-specific fields -->
                <div v-if="isInfluencer" class="influencer-details">
                  <hr>
                  <h4 class="mb-3">Influencer Information</h4>
                  
                  <div class="row mb-4">
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Influencer Name</h5>
                      <p class="fs-5">{{ profile.influencer_name || 'Not specified' }}</p>
                    </div>
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Category</h5>
                      <p class="fs-5">{{ profile.category || 'Not specified' }}</p>
                    </div>
                  </div>
                  
                  <div class="row mb-4">
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Niche</h5>
                      <p class="fs-5">{{ profile.niche || 'Not specified' }}</p>
                    </div>
                    <div class="col-md-6">
                      <h5 class="text-muted mb-2">Reach</h5>
                      <p class="fs-5">{{ profile.reach?.toLocaleString() || 'Not specified' }}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Edit Profile Mode -->
              <form v-if="isEditing && profile" @submit.prevent="saveProfile">
                <ApiError :error="error" v-if="error" @dismiss="error = ''" />
                
                <!-- Basic Information -->
                <div class="row mb-3">
                  <div class="col-md-6">
                    <label for="username" class="form-label">Username <span class="text-danger">*</span></label>
                    <input 
                      type="text" 
                      class="form-control" 
                      id="username" 
                      v-model="formData.username" 
                      :class="{'is-invalid': validationErrors.username}"
                      placeholder="Enter your username"
                    >
                    <div class="invalid-feedback" v-if="validationErrors.username">
                      {{ validationErrors.username }}
                    </div>
                  </div>
                  
                  <div class="col-md-6">
                    <label for="email" class="form-label">Email <span class="text-danger">*</span></label>
                    <input 
                      type="email" 
                      class="form-control" 
                      id="email" 
                      v-model="formData.email" 
                      :class="{'is-invalid': validationErrors.email}"
                      placeholder="Enter your email"
                    >
                    <div class="invalid-feedback" v-if="validationErrors.email">
                      {{ validationErrors.email }}
                    </div>
                  </div>
                </div>
                
                <div class="mb-3">
                  <label for="bio" class="form-label">Bio</label>
                  <textarea 
                    class="form-control" 
                    id="bio" 
                    v-model="formData.bio" 
                    rows="3"
                    placeholder="Tell us about yourself"
                  ></textarea>
                </div>
                
                <div class="mb-3">
                  <label for="avatar_url" class="form-label">Profile Picture URL</label>
                  <input 
                    type="url" 
                    class="form-control" 
                    id="avatar_url" 
                    v-model="formData.avatar_url" 
                    placeholder="URL to your profile picture"
                  >
                  <div class="form-text">Enter a URL to your profile image (optional)</div>
                </div>
                
                <!-- Sponsor-specific fields -->
                <div v-if="isSponsor" class="sponsor-edit">
                  <hr>
                  <h4 class="mb-3">Sponsor Information</h4>
                  
                  <div class="row mb-3">
                    <div class="col-md-6">
                      <label for="company_name" class="form-label">Company Name <span class="text-danger">*</span></label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="company_name" 
                        v-model="formData.company_name" 
                        :class="{'is-invalid': validationErrors.company_name}"
                        placeholder="Enter your company name"
                      >
                      <div class="invalid-feedback" v-if="validationErrors.company_name">
                        {{ validationErrors.company_name }}
                      </div>
                    </div>
                    
                    <div class="col-md-6">
                      <label for="industry" class="form-label">Industry <span class="text-danger">*</span></label>
                      <select 
                        class="form-select" 
                        id="industry" 
                        v-model="formData.industry"
                        :class="{'is-invalid': validationErrors.industry}"
                      >
                        <option value="" disabled>Select an industry</option>
                        <option v-for="option in industryOptions" :key="option" :value="option">
                          {{ option }}
                        </option>
                      </select>
                      <div class="invalid-feedback" v-if="validationErrors.industry">
                        {{ validationErrors.industry }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Influencer-specific fields -->
                <div v-if="isInfluencer" class="influencer-edit">
                  <hr>
                  <h4 class="mb-3">Influencer Information</h4>
                  
                  <div class="row mb-3">
                    <div class="col-md-6">
                      <label for="influencer_name" class="form-label">Influencer Name <span class="text-danger">*</span></label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="influencer_name" 
                        v-model="formData.influencer_name" 
                        :class="{'is-invalid': validationErrors.influencer_name}"
                        placeholder="Enter your influencer name"
                      >
                      <div class="invalid-feedback" v-if="validationErrors.influencer_name">
                        {{ validationErrors.influencer_name }}
                      </div>
                    </div>
                    
                    <div class="col-md-6">
                      <label for="category" class="form-label">Category <span class="text-danger">*</span></label>
                      <select 
                        class="form-select" 
                        id="category" 
                        v-model="formData.category"
                        :class="{'is-invalid': validationErrors.category}"
                      >
                        <option value="" disabled>Select your category</option>
                        <option v-for="option in categoryOptions" :key="option" :value="option">
                          {{ option }}
                        </option>
                      </select>
                      <div class="invalid-feedback" v-if="validationErrors.category">
                        {{ validationErrors.category }}
                      </div>
                    </div>
                  </div>
                  
                  <div class="row mb-3">
                    <div class="col-md-6">
                      <label for="niche" class="form-label">Niche</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="niche" 
                        v-model="formData.niche" 
                        placeholder="Describe your niche (e.g., Vegan Food, Tech Reviews)"
                      >
                    </div>
                    
                    <div class="col-md-6">
                      <label for="reach" class="form-label">Reach (Followers)</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        id="reach" 
                        v-model="formData.reach" 
                        min="0"
                        placeholder="Your total follower count"
                      >
                    </div>
                  </div>
                  
                  <div class="mb-3">
                    <label for="social_links" class="form-label">Social Media Links</label>
                    <textarea
                      class="form-control"
                      id="social_links"
                      v-model="formData.social_links"
                      rows="2"
                      placeholder="Enter your social media links (e.g., Instagram: @username, TikTok: @username)"
                    ></textarea>
                  </div>
                </div>
                
                <div class="d-flex justify-content-end mt-4">
                  <button type="button" class="btn btn-outline-secondary me-2" @click="toggleEdit">
                    Cancel
                  </button>
                  <button type="submit" class="btn btn-primary" :disabled="loading">
                    <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  animation: fadeIn 0.5s ease;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border: 4px solid #fff;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.avatar-container {
  position: relative;
  display: inline-block;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>

