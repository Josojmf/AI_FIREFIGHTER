/**
 * API Configuration - Auto-detection
 * ===================================
 * Este script detecta automáticamente la URL correcta del backend
 * basándose en el entorno (desarrollo, Docker, producción)
 */

(function() {
  'use strict';

  /**
   * Detectar la URL correcta del backend
   */
  function detectBackendURL() {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    console.log('🔍 Detectando configuración de API...');
    console.log(`   Hostname: ${hostname}`);
    console.log(`   Port: ${port}`);
    
    // Caso 1: Producción (IP pública o dominio)
    if (hostname === '167.71.63.108' || hostname.includes('firefighter')) {
      console.log('✅ Modo: PRODUCCIÓN');
      return 'http://167.71.63.108:5000';
    }
    
    // Caso 2: Docker local (navegador accediendo a través de puerto mapeado)
    if (port === '8080' && hostname === 'localhost') {
      console.log('✅ Modo: DOCKER LOCAL');
      return 'http://localhost:5000';
    }
    
    // Caso 3: Desarrollo local normal
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      console.log('✅ Modo: DESARROLLO LOCAL');
      return 'http://localhost:5000';
    }
    
    // Fallback: asumir desarrollo
    console.warn('⚠️  No se pudo detectar entorno, usando fallback');
    return 'http://localhost:5000';
  }

  /**
   * Configurar API_BASE_URL
   */
  window.API_BASE_URL = detectBackendURL();
  
  console.log('🔥 API_BASE_URL configurado:', window.API_BASE_URL);
  
  /**
   * Función helper para hacer peticiones a la API
   */
  window.apiRequest = async function(endpoint, options = {}) {
    const url = `${window.API_BASE_URL}${endpoint}`;
    
    console.log(`📡 API Request: ${options.method || 'GET'} ${url}`);
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };
    
    try {
      const response = await fetch(url, mergedOptions);
      
      console.log(`📡 API Response: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`❌ API Error: ${error.message}`);
      throw error;
    }
  };
  
  console.log('✅ API utilities loaded');
})();