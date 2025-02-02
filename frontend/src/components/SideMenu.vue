<template>
<div class="side-menu">
    <div class="logo-section">
    <h1>BudgetApp</h1>
    </div>
    <nav class="menu-items">
    <router-link to="/" class="menu-item">
        <i class="fas fa-home"></i>
        <span>Dashboard</span>
    </router-link>
    <router-link to="/create-budget" class="menu-item">
        <i class="fas fa-plus-circle"></i>
        <span>Create Budget</span>
    </router-link>
    </nav>
</div>
</template>

<script>
export default {
name: 'SideMenu',
}
</script>

<style scoped>
.side-menu {
width: 250px;
height: 100vh;
background-color: #2c3e50;
color: white;
position: fixed;
left: 0;
top: 0;
padding: 1rem;
}

.logo-section {
padding: 1rem 0;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
margin-bottom: 2rem;
}

.logo-section h1 {
margin: 0;
font-size: 1.5rem;
text-align: center;
}

.menu-items {
display: flex;
flex-direction: column;
gap: 0.5rem;
}

.menu-item {
display: flex;
align-items: center;
padding: 0.75rem 1rem;
color: white;
text-decoration: none;
border-radius: 0.25rem;
transition: background-color 0.3s;
}

.menu-item:hover {
background-color: rgba(255, 255, 255, 0.1);
}

.menu-item i {
margin-right: 0.75rem;
width: 20px;
}

.menu-item.router-link-active {
background-color: rgba(255, 255, 255, 0.2);
}
</style>

