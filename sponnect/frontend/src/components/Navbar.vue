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
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary sticky-top">
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
            <RouterLink class="nav-link" to="/influencer/ad-requests">My Requests</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/search/campaigns">Search Campaigns</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/influencer/campaigns/browse">Browse All Campaigns</RouterLink>
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
          <li class="nav-item">
            <RouterLink class="nav-link" to="/admin/reports">Reports</RouterLink>
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
</template>

<style scoped>
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