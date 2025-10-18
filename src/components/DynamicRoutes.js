import React from 'react';
import { Route } from 'react-router-dom';
import { getAvailableUrlPaths } from '../config/adminDivisions';
import MunicipalityDashboard from '../pages/MunicipalityDashboard';
import ThreadsPage from '../pages/ThreadsPage';
import ThreadDetail from './social/ThreadDetail';

/**
 * Generate dynamic routes based on available administrative division data.
 * This ensures that only countries with actual data get routing support.
 *
 * Generated routes:
 * - /{adminPath}/:slug
 * - /{adminPath}/:slug/:section
 *
 * Where adminPath is dynamically determined from available country data
 * (e.g., 'municipality', 'commune', 'city', etc.)
 */
export const generateDynamicRoutes = () => {
  // Get all unique URL paths from countries that have data
  const availableUrlPaths = getAvailableUrlPaths();

  // Log the dynamically generated routes for debugging  availableUrlPaths.forEach(path => {  });

  const routes = [];

  // Dynamically generated routes based on available data
  availableUrlPaths.forEach((urlPath) => {
    routes.push(
      // Main dashboard route
      <Route
        key={`${urlPath}-base`}
        path={`/${urlPath}/:municipalitySlug`}
        element={<MunicipalityDashboard />}
      />,
      // Section route
      <Route
        key={`${urlPath}-section`}
        path={`/${urlPath}/:municipalitySlug/:section`}
        element={<MunicipalityDashboard />}
      />,
      // Threads list route
      <Route
        key={`${urlPath}-threads`}
        path={`/${urlPath}/:municipalitySlug/threads`}
        element={<ThreadsPage />}
      />,
      // Thread detail route
      <Route
        key={`${urlPath}-thread-detail`}
        path={`/${urlPath}/:municipalitySlug/thread/:threadId`}
        element={<ThreadDetail />}
      />
    );
  });

  return routes;
};