<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount } from 'vue';
import type { application } from '../api/models';
import api from '../api/api';
import router from '../routes/router';

const applications = ref<application[]>([]);
const ascending = ref(true);

onMounted(async () => {
  const res = await api.get('/applications');
  applications.value = res.data;
});

const statusClass = (status: string) => {
  switch (status.toLowerCase()) {
    case 'awaiting reply': return 'yellow';
    case 'accepted': return 'green';
    case 'rejected': return 'red';
    default: return 'gray';
  }
};

const STATUSES = ["None", "awaiting reply", "accepted", "rejected"] as const;
type Status = (typeof STATUSES)[number];
const shownStatus = ref<Status>("None");

const filteredApplications = computed(() => {
  if (shownStatus.value === "None") return applications.value;
  return applications.value.filter(
    (app) => app.status.toLowerCase() === shownStatus.value.toLowerCase()
  );
});

const sortedApplications = computed(() => {
  return [...filteredApplications.value].sort((a, b) => {
    const dateA = new Date(a.sent_date).getTime();
    const dateB = new Date(b.sent_date).getTime();
    return ascending.value ? dateA - dateB : dateB - dateA;
  });
});

const toggleSort = () => {
  ascending.value = !ascending.value;
};

// Close dropdown when clicking outside
const showDropdown = ref(false);
const dropdown = ref<HTMLElement | null>(null);

function toggleDropdown() {
  showDropdown.value = !showDropdown.value;
}

function selectStatus(status: Status) {
  shownStatus.value = status;
  showDropdown.value = false;
}

function handleClickOutside(event: MouseEvent) {
  if (dropdown.value && !dropdown.value.contains(event.target as Node)) {
    showDropdown.value = false;
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside));
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside));


function gotoCompanyTimeline(companyName: string){
  router.push({name: "CompanyTimeline", params: {companyName} })
}

</script>


<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="dashboard-header">
      <div>
        <h1>Internship Dashboard</h1>
        <span>{{ applications.length }} Applications</span>
      </div>

      <div class="controls">
        <!-- Status Filter Dropdown -->
        <div class="filter-dropdown" @click="toggleDropdown" ref="dropdown">
          <button class="dropdown-btn">
            Filter: {{ shownStatus === 'None' ? 'All' : shownStatus }}
            <span class="arrow">{{ showDropdown ? '▲' : '▼' }}</span>
          </button>

          <div v-if="showDropdown" class="dropdown-menu">
            <label
              v-for="status in STATUSES"
              :key="status"
              class="dropdown-option"
              @click.stop="selectStatus(status)"
            >
              {{ status }}
            </label>
          </div>
        </div>

        <button class="sort-btn" @click="toggleSort">
          Sort by Date: {{ ascending ? 'Oldest → Newest' : 'Newest → Oldest' }}
        </button>
      </div>
    </header>

    <!-- Grid -->
    <div class="grid">
      <div  @click="gotoCompanyTimeline(app.company_name)" v-for="app in sortedApplications" :key="app.id" class="card">
        <div class="card-header">
          <h2>{{ app.company_name }}</h2>
          <span :class="['status', statusClass(app.status)]">{{ app.status }}</span>
        </div>
        <p class="position">{{ app.position }}</p>
        <p class="sent-date">Sent: {{ new Date(app.sent_date).toLocaleDateString() }}</p>
        <p class="summary">{{ app.summary }}</p>
      </div>
    </div>
  </div>
</template>


<style>

body {
  font-family: 'Inter', sans-serif;
  margin: 0;
  background: #f4f6f8;
}
.dashboard {
  padding: 2rem;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.dashboard-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.dashboard-header span {
  font-size: 1rem;
  color: #7f8c8d;
}

.controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

/* Filter Dropdown */
.filter-dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-btn {
  background: white;
  border: 1px solid #d1d5db;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #34495e;
  transition: background 0.2s;
}

.dropdown-btn:hover {
  background: #f1f5f9;
}

.arrow {
  margin-left: 6px;
  font-size: 0.8rem;
}

.dropdown-menu {
  position: absolute;
  top: 110%;
  left: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  z-index: 1000;
  width: 150px;
  padding: 0.5rem 0;
}

.dropdown-option {
  display: block;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #374151;
  transition: background 0.15s;
}

.dropdown-option:hover {
  background: #f3f4f6;
}

.sort-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  background-color: #2980b9;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.sort-btn:hover {
  background-color: #1c5980;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

/* Card */
.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2980b9;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status.yellow { background: #fef3c7; color: #b45309; }
.status.green { background: #d1fae5; color: #065f46; }
.status.red { background: #fee2e2; color: #b91c1c; }
.status.gray { background: #e5e7eb; color: #374151; }

.position {
  font-weight: 500;
  color: #34495e;
  margin-bottom: 0.25rem;
}

.sent-date {
  font-size: 0.75rem;
  color: #7f8c8d;
  margin-bottom: 0.75rem;
}

.summary {
  font-size: 0.875rem;
  color: #2c3e50;
  line-height: 1.4;
}
</style>