import React from 'react';
import { Route } from 'react-router-dom';
import { getAvailableUrlPaths } from '../config/adminDivisions';
import MunicipalityDashboard from '../pages/MunicipalityDashboard';

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

  // Log the dynamically generated routes for debugging
  console.log('🚀 Dynamic Routes Generated for:', availableUrlPaths);
  console.log('📍 Route patterns created:');
  availableUrlPaths.forEach(path => {
    console.log(`   • /${path}/:municipalitySlug`);
    console.log(`   • /${path}/:municipalitySlug/:section`);
  });

  const routes = [];

  // Dynamically generated routes based on available data
  availableUrlPaths.forEach((urlPath) => {
    routes.push(
      <Route
        key={`${urlPath}-base`}
        path={`/${urlPath}/:municipalitySlug`}
        element={<MunicipalityDashboard />}
      />,
      <Route
        key={`${urlPath}-section`}
        path={`/${urlPath}/:municipalitySlug/:section`}
        element={<MunicipalityDashboard />}
      />
    );
  });

  return routes;
};