import { createRouter, createWebHistory } from "vue-router";

import Dashboard from "../views/DashboardView.vue";
import CompanyTimeLine from "../views/CompanyTimeLineView.vue";

const routes = [
  {
    path: "/",
    name: "Dashboard",
    component: Dashboard,
  },
  {
    path: "/company/:companyName", // /company/:id
    name: "CompanyTimeline",
    component: CompanyTimeLine,
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
