<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const isLoggedIn = computed(() => authStore.isAuthenticated)
const userRole = computed(() => authStore.userRole)
const userName = computed(() => {
  if (authStore.user) {
    // For sponsors, prefer company_name
    if (userRole.value === 'sponsor' && authStore.user.company_name) {
      return authStore.user.company_name
    }
    // For influencers, prefer influencer_name
    if (userRole.value === 'influencer' && authStore.user.influencer_name) {
      return authStore.user.influencer_name
    }
    // Fall back to username
    return authStore.user.username || 'User'
  }
  return 'User'
})

const logout = () => {
  authStore.logout()
}

// Initialize Bootstrap dropdowns properly
onMounted(() => {
  try {
    // Check if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
      // Get all dropdowns on the page
      const dropdownElementList = document.querySelectorAll('.dropdown-toggle')
      
      // Initialize each dropdown
      const dropdownList = [...dropdownElementList].map(dropdownToggleEl => {
        return new bootstrap.Dropdown(dropdownToggleEl, {
          // Prevent dropdown from closing when clicking inside
          autoClose: 'outside'  
        })
      })
      
      console.log('Dropdowns initialized:', dropdownList.length)
    } else {
      console.warn('Bootstrap JS not loaded, dropdowns may not work correctly')
    }
  } catch (err) {
    console.error('Error initializing dropdowns:', err)
  }
})
</script>

<template>
  <div class="navbar-container">
    <!-- Background image container -->
    <div class="image-background">
      <img 
        src="https://res.cloudinary.com/da9hk6mws/image/upload/v1746987905/videoframe_3455_ry6k3c.png"
        alt="Navbar Background"
      />
      <div class="overlay"></div>
    </div>
    
    <!-- Actual navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
      <div class="container">
        <RouterLink class="navbar-brand fw-bold" to="/">
          <i class="bi bi-link-45deg me-2"></i>Sponnect
        </RouterLink>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
          <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarContent">
          <!-- Public links -->
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/">Home</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/about">About</RouterLink>
            </li>
          </ul>
          
          <!-- Not logged in -->
          <ul class="navbar-nav ms-auto" v-if="!isLoggedIn">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/login">Login</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="btn btn-light ms-2" to="/register">Register</RouterLink>
            </li>
          </ul>
          
          <!-- Logged in as Sponsor -->
          <ul class="navbar-nav ms-auto" v-else-if="userRole === 'sponsor'">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/sponsor/dashboard">Dashboard</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/sponsor/campaigns">Campaigns</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/sponsor/ad-requests">Ad Requests</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/search/influencers">Find Influencers</RouterLink>
            </li>
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="bi bi-person-circle me-1"></i>{{ userName }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><RouterLink class="dropdown-item" to="/profile"><i class="bi bi-person me-2"></i>Profile</RouterLink></li>
                <li><RouterLink class="dropdown-item" to="/sponsor/campaigns/create"><i class="bi bi-plus-circle me-2"></i>New Campaign</RouterLink></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="logout"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
              </ul>
            </li>
          </ul>
          
          <!-- Logged in as Influencer -->
          <ul class="navbar-nav ms-auto" v-else-if="userRole === 'influencer'">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/influencer/dashboard">Dashboard</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/influencer/ad-requests">Ad Requests</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/influencer/campaigns/browse">Browse Campaigns</RouterLink>
            </li>
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="bi bi-person-circle me-1"></i>{{ userName }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><RouterLink class="dropdown-item" to="/profile"><i class="bi bi-person me-2"></i>Profile</RouterLink></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="logout"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
              </ul>
            </li>
          </ul>
          
          <!-- Logged in as Admin -->
          <ul class="navbar-nav ms-auto" v-else-if="userRole === 'admin'">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/admin/dashboard">Dashboard</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/admin/users">Users</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/admin/campaigns">Campaigns</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/admin/statistics">Statistics</RouterLink>
            </li>
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                <i class="bi bi-person-circle me-1"></i>Admin
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><RouterLink class="dropdown-item" to="/profile"><i class="bi bi-person me-2"></i>Profile</RouterLink></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="logout"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.navbar-container {
  position: relative;
}

.image-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.image-background img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.733); /* Dark overlay */
}

.navbar {
  background-color: transparent !important;
  position: relative;
  z-index: 100; /* Increase z-index for proper stacking */
}

.dropdown-menu {
  z-index: 9999;
  border-radius: 0.5rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  border: none;
  padding: 0.5rem 0;
}

.dropdown-item {
  padding: 0.5rem 1rem;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item i {
  color: #6c757d;
}

.nav-link{
  color: white;
}

.nav-link.router-link-active {
  font-weight: bold;
  position: relative;
}

.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: white;
}

.navbar-brand {
  font-size: 1.5rem;
}

/* Fix dropdown on mobile screens */
@media (max-width: 992px) {
  .navbar-nav {
    padding: 1rem 0;
  }
  
  .nav-item {
    margin-bottom: 0.5rem;
  }
  
  .dropdown-menu {
    background-color: rgba(0, 0, 0, 0.1);
    border: none;
    box-shadow: none;
    position: static !important;
    width: 100%;
    margin-top: 0;
    padding-left: 1rem;
  }
  
  .dropdown-item {
    color: white;
  }
  
  .dropdown-item:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: white;
  }
  
  .dropdown-item i {
    color: white;
  }
}
</style> 