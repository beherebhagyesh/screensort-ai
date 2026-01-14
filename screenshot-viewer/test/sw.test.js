const request = require('supertest');
const app = require('../server');
const fs = require('fs');
const path = require('path');

describe('Service Worker', () => {
  it('should serve the service-worker.js file', async () => {
    const res = await request(app).get('/service-worker.js');
    expect(res.statusCode).toEqual(200);
    expect(res.header['content-type']).toMatch(/javascript/);
  });

  it('should contain cache configuration', () => {
    const swContent = fs.readFileSync(path.join(__dirname, '../public/service-worker.js'), 'utf8');
    expect(swContent).toContain('CACHE_NAME');
    expect(swContent).toContain('STATIC_ASSETS');
    expect(swContent).toContain('Network-first'); // My comment in the code
  });
});
