/**
 * Demo: Dynamic Routes System
 *
 * This file demonstrates how the dynamic routing system automatically
 * generates routes when new countries are added.
 *
 * Run this file in the browser console to see the system in action.
 */

import { addCountryWithCommonType, logCurrentRoutes, SETUP_INSTRUCTIONS } from './countryUtils';
import { getAvailableUrlPaths, getAvailableCountries } from './adminDivisions';

/**
 * Demo function - shows before and after adding new countries
 */
export const runDemo = () => {  logCurrentRoutes();  addCountryWithCommonType('SN', 'Senegal', 'commune', 'communes_senegal.json');  addCountryWithCommonType('DE', 'Germany', 'gemeinde', 'gemeinden_germany.json');  logCurrentRoutes();};

/**
 * Test URL generation for different countries
 */
export const testUrlGeneration = () => {
  const { getMunicipalityUrl } = require('../data/municipalitiesUtils');
  const { setCurrentCountry } = require('./adminDivisions');
  // Test Canada (default)
  setCurrentCountry('CA');
  // Test Benin
  setCurrentCountry('BJ');
  // Future countries would work the same way};

export default { runDemo, testUrlGeneration };