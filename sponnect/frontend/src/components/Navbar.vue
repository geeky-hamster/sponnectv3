<script setup>
import { computed } from 'vue'
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
</script>

<template>
  <div class="navbar-container">
    <!-- Background video container -->
    <div class="video-background">
      <video 
        autoplay 
        loop 
        muted 
        playsinline
        src="https://video.wixstatic.com/video/11062b_0a3a288182c34d1294f46fe6a2b17df6/1080p/mp4/file.mp4">
      </video>
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

.video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.video-background video {
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
  background-color: rgba(0, 0, 0, 0.733); /* Primary blue with opacity */
}

.navbar {
  background-color: transparent !important;
  position: relative;
  z-index: 1;
}

.dropdown-menu {
  z-index: 9999;
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

@media (max-width: 992px) {
  .navbar-nav {
    padding: 1rem 0;
  }
  
  .nav-item {
    margin-bottom: 0.5rem;
  }
}
</style> 