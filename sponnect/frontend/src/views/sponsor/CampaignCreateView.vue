<script setup>
import { ref, reactive } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { sponsorService } from '../../services/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')

// Form state
const form = reactive({
  name: '',
  description: '',
  goals: '',
  budget: '',
  start_date: '',
  end_date: '',
  visibility: 'private'
})

// Form validation
const validationErrors = reactive({
  name: '',
  budget: '',
  start_date: ''
})

// Check if form is valid
const isFormValid = () => {
  let valid = true
  
  // Reset validation errors
  validationErrors.name = ''
  validationErrors.budget = ''
  validationErrors.start_date = ''
  
  // Validate name
  if (!form.name.trim()) {
    validationErrors.name = 'Campaign name is required'
    valid = false
  }
  
  // Validate budget
  if (!form.budget) {
    validationErrors.budget = 'Budget is required'
    valid = false
  } else if (isNaN(parseFloat(form.budget)) || parseFloat(form.budget) <= 0) {
    validationErrors.budget = 'Budget must be a positive number'
    valid = false
  }
  
  // Validate start date
  if (!form.start_date) {
    validationErrors.start_date = 'Start date is required'
    valid = false
  }
  
  // Additional validation: end date must be after start date if provided
  if (form.end_date && form.start_date && new Date(form.end_date) <= new Date(form.start_date)) {
    validationErrors.end_date = 'End date must be after start date'
    valid = false
  }
  
  return valid
}

// Set today's date as min date for date inputs
const today = new Date().toISOString().split('T')[0]

// Handle form submission
const handleSubmit = async () => {
  if (!isFormValid()) return
  
  loading.value = true
  error.value = ''
  
  try {
    // Format budget as number for API
    const formData = {
      ...form,
      budget: parseFloat(form.budget)
    }
    
    const response = await sponsorService.createCampaign(formData)
    
    // Navigate to the new campaign's detail page
    router.push(`/sponsor/campaigns/${response.data.campaign.id}`)
  } catch (err) {
    console.error('Failed to create campaign:', err)
    error.value = 'Failed to create campaign. Please check your inputs and try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="campaign-create-view py-5">
    <div class="container">
      <!-- Breadcrumb -->
      <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/dashboard">Dashboard</RouterLink>
          </li>
          <li class="breadcrumb-item">
            <RouterLink to="/sponsor/campaigns">Campaigns</RouterLink>
          </li>
          <li class="breadcrumb-item active">Create Campaign</li>
        </ol>
      </nav>
      
      <h1 class="mb-4">Create New Campaign</h1>
      
      <!-- Error alert -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = ''"></button>
      </div>
      
      <!-- Campaign form -->
      <div class="card border-0 shadow-sm">
        <div class="card-body p-4">
          <form @submit.prevent="handleSubmit">
            <div class="row g-4">
              <!-- Basic information -->
              <div class="col-md-8">
                <div class="card-title h5 mb-4">Basic Information</div>
                
                <div class="mb-3">
                  <label for="campaignName" class="form-label">Campaign Name <span class="text-danger">*</span></label>
                  <input
                    type="text"
                    class="form-control"
                    id="campaignName"
                    v-model="form.name"
                    :class="{ 'is-invalid': validationErrors.name }"
                    placeholder="Enter a memorable name for your campaign"
                  >
                  <div class="invalid-feedback">{{ validationErrors.name }}</div>
                </div>
                
                <div class="mb-3">
                  <label for="campaignDescription" class="form-label">Description</label>
                  <textarea
                    class="form-control"
                    id="campaignDescription"
                    v-model="form.description"
                    rows="4"
                    placeholder="Describe your campaign and what you're looking for"
                  ></textarea>
                </div>
                
                <div class="mb-3">
                  <label for="campaignGoals" class="form-label">Goals</label>
                  <textarea
                    class="form-control"
                    id="campaignGoals"
                    v-model="form.goals"
                    rows="3"
                    placeholder="What are your goals for this campaign?"
                  ></textarea>
                </div>
              </div>
              
              <!-- Settings -->
              <div class="col-md-4">
                <div class="card-title h5 mb-4">Settings</div>
                
                <div class="mb-3">
                  <label for="campaignBudget" class="form-label">Budget ($) <span class="text-danger">*</span></label>
                  <input
                    type="number"
                    class="form-control"
                    id="campaignBudget"
                    v-model="form.budget"
                    :class="{ 'is-invalid': validationErrors.budget }"
                    min="1"
                    step="1"
                    placeholder="Total budget in USD"
                  >
                  <div class="invalid-feedback">{{ validationErrors.budget }}</div>
                </div>
                
                <div class="mb-3">
                  <label for="campaignStartDate" class="form-label">Start Date <span class="text-danger">*</span></label>
                  <input
                    type="date"
                    class="form-control"
                    id="campaignStartDate"
                    v-model="form.start_date"
                    :class="{ 'is-invalid': validationErrors.start_date }"
                    :min="today"
                  >
                  <div class="invalid-feedback">{{ validationErrors.start_date }}</div>
                </div>
                
                <div class="mb-3">
                  <label for="campaignEndDate" class="form-label">End Date</label>
                  <input
                    type="date"
                    class="form-control"
                    id="campaignEndDate"
                    v-model="form.end_date"
                    :class="{ 'is-invalid': validationErrors.end_date }"
                    :min="form.start_date || today"
                  >
                  <div class="invalid-feedback">{{ validationErrors.end_date }}</div>
                  <div class="form-text">Optional. Leave blank for ongoing campaigns.</div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label">Visibility</label>
                  <div class="form-check">
                    <input
                      class="form-check-input"
                      type="radio"
                      name="visibility"
                      id="visibilityPrivate"
                      value="private"
                      v-model="form.visibility"
                    >
                    <label class="form-check-label" for="visibilityPrivate">
                      <i class="bi bi-eye-slash me-1"></i> Private
                      <div class="form-text">Only visible to influencers you invite</div>
                    </label>
                  </div>
                  <div class="form-check mt-2">
                    <input
                      class="form-check-input"
                      type="radio"
                      name="visibility"
                      id="visibilityPublic"
                      value="public"
                      v-model="form.visibility"
                    >
                    <label class="form-check-label" for="visibilityPublic">
                      <i class="bi bi-eye me-1"></i> Public
                      <div class="form-text">Visible to all influencers who can apply to your campaign</div>
                    </label>
                  </div>
                </div>
              </div>
              
              <!-- Form buttons -->
              <div class="col-12 d-flex justify-content-end border-top pt-4">
                <RouterLink to="/sponsor/campaigns" class="btn btn-outline-secondary me-2">
                  Cancel
                </RouterLink>
                <button
                  type="submit"
                  class="btn btn-primary"
                  :disabled="loading"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                  Create Campaign
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.campaign-create-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 