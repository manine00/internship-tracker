<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { Company } from "../api/models";
import api from "../api/api";
import { useRoute } from "vue-router";

const route = useRoute();
const company = ref<Company|null>(null);

onMounted(async () => {
      const companyName = route.params.companyName;
      const result = await api.get(`/company/${companyName}`);
      company.value = result.data 
      //console.log(company.value);
});

const description = ref<string>("");

async function submitDescription() {
  try {
    if (!company.value) throw new Error("No company selected");
    await api.post(
      `/company/description/${company.value.name}`,
      { summary: description.value } 
    );
    alert("Description submitted successfully!");
    description.value = "";
  } catch (e: any) {
    console.error(e);
    alert(e.response?.data?.detail || "Failed to submit description");
  }
}
async function autosubmition(){
  try {
    if (!company.value) throw new Error("No company selected");
    await api.post(
      `/company/description/${company.value.name}` 
    );
    alert("auto submition from timeline!");
    description.value = "";
  } catch (e: any) {
    console.error(e);
    alert(e.response?.data?.detail || "Failed to submit description");
  }
}
function parseDescription(text: string): Record<string, string | string[]> {
  const result: Record<string, string | string[]> = {};
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  let currentKey: string | null = null;

  for (const line of lines) {
    const match = line.match(/^- \*\*(.+?)\*\*: ?(.*)$/);

    if (match !== null) {
      const [, rawKey, rawValue] = match; // destructure safely
      if (!rawKey) continue; // defensive check

      currentKey = rawKey.toLowerCase().replace(/\s+/g, "_");
      const value = rawValue?.trim();

      if (value) {
        result[currentKey] = value;
        currentKey = null;
      } else {
        result[currentKey] = [];
      }
      continue;
    }

    if (currentKey && line.startsWith("-")) {
      const subItem = line.replace(/^-\s*/, "").trim();
      const existing = result[currentKey];
      if (Array.isArray(existing)) existing.push(subItem);
      else result[currentKey] = [subItem];
      continue;
    }

    if (currentKey) {
      const existing = result[currentKey];
      if (Array.isArray(existing)) existing.push(line);
      else if (typeof existing === "string") result[currentKey] = existing + " " + line;
      else result[currentKey] = line;
    }
  }

  return result;
}

const sortedTimeline = computed(() =>
  [...(company.value?.timeline || [])].sort(
    (a, b) => new Date(b.sent_date).getTime() - new Date(a.sent_date).getTime()
  )
);

</script>

<template>
  <div v-if="company" class="company-overview">

    <header class="header">
  <h1>{{ company.name }}</h1>

  <div v-if="company.internship_description" class="description">
    <div
      v-for="(value, key) in parseDescription(company.internship_description)"
      :key="key"
      class="description-section"
    >
      <h3 class="description-title">
        {{ key.replace(/_/g, ' ') }}
      </h3>
      <div class="description-content">
        <template v-if="Array.isArray(value)">
          <ul>
            <li v-for="(item, index) in value" :key="index">{{ item }}</li>
          </ul>
        </template>
        <template v-else>
          <p>{{ value }}</p>
        </template>
      </div>
    </div>
  </div>

  <div v-else class="fill-description-form">
    <textarea
      v-model="description"
      placeholder="Enter internship description..."
      rows="5"
    ></textarea>
    <div class="submit">
      <button @click="autosubmition">autofill</button>
      <button @click="submitDescription" :disabled="!description.trim()">
        Submit
      </button>
    </div>
  </div>
</header>

    <section class="timeline-section">
      <h2>Timeline of Exchanges</h2>
      <div class="timeline">
        <div
          v-for="(event, index) in sortedTimeline"
          :key="index"
          class="timeline-item"
        >
          <div class="timeline-marker"></div>
          <div class="timeline-content">
            <div class="timeline-header">
              <h3>{{ event.position }}</h3>
              <span>{{ new Date(event.sent_date).toLocaleDateString() }}</span>
            </div>
            <p>{{ event.summary }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>

  <div v-else class="loading">Loading company data...</div>
</template>

<style scoped>
.company-overview {
  font-family: "Inter", sans-serif;
  background-color: #f7f8fa;
  padding: 2rem;
  min-height: 100vh;
  color: #2c3e50;
}

/* Header */
.header {
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2.2rem;
  margin: 0 0 0.5rem;
  color: #1a237e;
}

.header p {
  color: #555;
  max-width: 800px;
  line-height: 1.6;
}

escription {
  margin-top: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.description-section + .description-section {
  margin-top: 1rem;
  border-top: 1px solid #ddd;
  padding-top: 1rem;
}

.description-title {
  font-weight: 600;
  text-transform: capitalize;
  margin-bottom: 0.5rem;
  color: #333;
}

.description-content ul {
  list-style-type: disc;
  margin-left: 1.5rem;
  color: #555;
}

.description-content p {
  margin: 0;
  color: #555;
}


.fill-description-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 600px;
  margin: 1rem auto;
}

textarea {
  resize: vertical;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
  min-height: 120px;
}

.submit {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.submit button {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.submit button:hover {
  background-color: #2c80ba;
}

.submit button:active {
  transform: scale(0.97);
}

.submit button:disabled {
  background-color: #a0a0a0;
  cursor: not-allowed;
}

/* Optional: different color for autofill button */
.submit button:first-of-type {
  background-color: #6c757d;
}

.submit button:first-of-type:hover {
  background-color: #5a6268;
}

/* Stats */
.stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1 1 200px;
  background: #fff;
  border-radius: 8px;
  padding: 1.2rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-card h2 {
  font-size: 0.9rem;
  color: #757575;
  margin-bottom: 0.4rem;
}

.stat-card p {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1565c0;
}

/* Timeline */
.timeline-section h2 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  color: #1a237e;
}

.timeline {
  position: relative;
  margin-left: 2rem;
  padding-left: 1rem;
  border-left: 3px solid #c5cae9;
}

.timeline-item {
  position: relative;
  margin-bottom: 2rem;
}

.timeline-marker {
  position: absolute;
  left: -1.1rem;
  top: 0.4rem;
  width: 14px;
  height: 14px;
  background-color: #3f51b5;
  border-radius: 50%;
  box-shadow: 0 0 0 3px #e8eaf6;
}

.timeline-content {
  background: #fff;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  box-shadow: 0 2px 8px rgba(63, 81, 181, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.timeline-content:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(63, 81, 181, 0.15);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.timeline-header h3 {
  margin: 0;
  color: #3f51b5;
  font-size: 1.1rem;
}

.timeline-header span {
  font-size: 0.85rem;
  color: #757575;
}

.timeline-content p {
  margin: 0;
  line-height: 1.5;
  color: #444;
}

.loading {
  text-align: center;
  margin-top: 4rem;
  color: #666;
}
</style>