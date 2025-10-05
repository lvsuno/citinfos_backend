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
export const runDemo = () => {
  console.log('🎬 DYNAMIC ROUTING SYSTEM DEMO');
  console.log('================================\n');

  console.log('📊 BEFORE - Current available routes:');
  logCurrentRoutes();
  console.log('\n' + '='.repeat(50) + '\n');

  console.log('➕ ADDING: Senegal with communes...');
  addCountryWithCommonType('SN', 'Senegal', 'commune', 'communes_senegal.json');

  console.log('\n➕ ADDING: Germany with gemeinden...');
  addCountryWithCommonType('DE', 'Germany', 'gemeinde', 'gemeinden_germany.json');

  console.log('\n📊 AFTER - New routes automatically generated:');
  logCurrentRoutes();

  console.log('\n🎯 EXAMPLES OF AUTOMATICALLY GENERATED URLS:');
  console.log('  • Canada: /municipality/sherbrooke/accueil');
  console.log('  • Benin: /commune/cotonou/accueil');
  console.log('  • Senegal: /commune/dakar/accueil (NEW!)');
  console.log('  • Germany: /gemeinde/berlin/accueil (NEW!)');

  console.log('\n' + SETUP_INSTRUCTIONS);
};

/**
 * Test URL generation for different countries
 */
export const testUrlGeneration = () => {
  const { getMunicipalityUrl } = require('../data/municipalitiesUtils');
  const { setCurrentCountry } = require('./adminDivisions');

  console.log('🧪 TESTING URL GENERATION:\n');

  // Test Canada (default)
  setCurrentCountry('CA');
  console.log('🇨🇦 Canada:', getMunicipalityUrl('Sherbrooke'));

  // Test Benin
  setCurrentCountry('BJ');
  console.log('🇧🇯 Benin:', getMunicipalityUrl('Cotonou'));

  // Future countries would work the same way
  console.log('\n✨ Future countries will work automatically!');
};

export default { runDemo, testUrlGeneration };