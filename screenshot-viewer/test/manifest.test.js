const request = require('supertest');
const app = require('../server');

describe('PWA Manifest', () => {
  it('should serve the manifest file', async () => {
    const res = await request(app).get('/manifest.json');
    expect(res.statusCode).toEqual(200);
    expect(res.header['content-type']).toMatch(/json/);
  });

  it('should have correct dark mode colors', async () => {
    const res = await request(app).get('/manifest.json');
    const manifest = res.body;
    expect(manifest.background_color).toBe('#121212');
    expect(manifest.theme_color).toBe('#1e1e1e');
  });

  it('should have required PWA fields', async () => {
    const res = await request(app).get('/manifest.json');
    const manifest = res.body;
    expect(manifest.name).toBeDefined();
    expect(manifest.icons).toBeInstanceOf(Array);
    expect(manifest.start_url).toBe('/');
    expect(manifest.display).toBe('standalone');
  });
});
