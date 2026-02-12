#!/usr/bin/env node
/**
 * öffentlichevergabe.de API-Zugriff via Playwright
 * 
 * INSTALLATION (auf deinem Computer):
 * 1. npm install playwright
 * 2. npx playwright install chromium
 * 3. node api_access_local.js
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;

async function extractSwaggerSpec() {
    console.log('\n' + '='.repeat(80));
    console.log('SWAGGER-UI ANALYSE MIT PLAYWRIGHT');
    console.log('='.repeat(80));
    
    const browser = await chromium.launch({ headless: false }); // headless: false zum Debugging
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });
    const page = await context.newPage();
    
    const swaggerUrl = 'https://www.oeffentlichevergabe.de/documentation/swagger-ui/opendata/index.html';
    
    console.log(`\n📄 Lade Swagger-UI: ${swaggerUrl}`);
    
    try {
        // Seite laden
        await page.goto(swaggerUrl, { waitUntil: 'networkidle', timeout: 60000 });
        console.log('✅ Seite geladen');
        
        // Warte auf Swagger-UI
        await page.waitForTimeout(5000);
        
        // Methode 1: API-Spec via window.ui extrahieren
        console.log('\n🔍 Extrahiere API-Spezifikation...');
        
        const spec = await page.evaluate(() => {
            try {
                if (window.ui && window.ui.specSelectors) {
                    return window.ui.specSelectors.specJson().toJSON();
                }
                return null;
            } catch (e) {
                return { error: e.toString() };
            }
        });
        
        if (spec && !spec.error) {
            console.log('✅ API-Spezifikation extrahiert!');
            
            // Speichern
            await fs.writeFile(
                'swagger_spec.json',
                JSON.stringify(spec, null, 2),
                'utf-8'
            );
            console.log('💾 Gespeichert: swagger_spec.json');
            
            // Endpunkte anzeigen
            if (spec.paths) {
                console.log(`\n📊 Gefundene API-Endpunkte (${Object.keys(spec.paths).length}):`);
                
                Object.entries(spec.paths).slice(0, 20).forEach(([path, methods]) => {
                    console.log(`\n   ${path}:`);
                    Object.keys(methods).forEach(method => {
                        if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
                            const operation = methods[method];
                            console.log(`      • ${method.toUpperCase()}: ${operation.summary || ''}`);
                        }
                    });
                });
            }
            
            // Base URL extrahieren
            if (spec.servers && spec.servers.length > 0) {
                console.log(`\n🌐 API Base URL: ${spec.servers[0].url}`);
            }
            
            return spec;
        }
        
        // Methode 2: Network Requests abfangen
        console.log('\n⚠️  Spec nicht via window.ui gefunden, analysiere Network Requests...');
        
        const apiCalls = [];
        page.on('response', response => {
            const url = response.url();
            if (url.includes('/api/') || url.includes('opendata')) {
                apiCalls.push({
                    url: url,
                    status: response.status(),
                    contentType: response.headers()['content-type']
                });
            }
        });
        
        // Interagiere mit Swagger-UI um API-Calls zu triggern
        await page.waitForTimeout(3000);
        
        // Versuche, einen Endpunkt zu expandieren
        const firstEndpoint = await page.$('.opblock');
        if (firstEndpoint) {
            await firstEndpoint.click();
            await page.waitForTimeout(2000);
        }
        
        if (apiCalls.length > 0) {
            console.log(`\n✅ ${apiCalls.length} API-Calls gefunden:`);
            apiCalls.forEach(call => {
                console.log(`   • ${call.status} ${call.url}`);
            });
        }
        
        // Screenshot
        await page.screenshot({ path: 'swagger_ui.png', fullPage: true });
        console.log('\n📸 Screenshot: swagger_ui.png');
        
        return spec;
        
    } catch (error) {
        console.error(`\n❌ Fehler: ${error.message}`);
        await page.screenshot({ path: 'error.png' });
        return null;
    } finally {
        await browser.close();
    }
}

async function testDirectAPICall(spec) {
    console.log('\n' + '='.repeat(80));
    console.log('DIREKTE API-CALLS');
    console.log('='.repeat(80));
    
    if (!spec || !spec.servers || !spec.paths) {
        console.log('\n⚠️  Keine API-Spec verfügbar, überspringe direkte Calls');
        return;
    }
    
    const baseUrl = spec.servers[0].url;
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Teste erste paar GET-Endpunkte
    const getEndpoints = Object.entries(spec.paths)
        .filter(([path, methods]) => methods.get)
        .slice(0, 5);
    
    console.log(`\n🔍 Teste ${getEndpoints.length} GET-Endpunkte...\n`);
    
    for (const [path, methods] of getEndpoints) {
        const url = `${baseUrl}${path}`;
        console.log(`   ${path}:`);
        
        try {
            const response = await page.goto(url, { timeout: 10000 });
            
            if (response.status() === 200) {
                const contentType = response.headers()['content-type'];
                
                if (contentType && contentType.includes('json')) {
                    const data = await response.json();
                    console.log(`      ✅ 200 OK - JSON (${JSON.stringify(data).length} bytes)`);
                    
                    // Speichere erste erfolgreiche Response
                    if (Object.keys(data).length > 0) {
                        await fs.writeFile(
                            `sample_${path.replace(/\//g, '_')}.json`,
                            JSON.stringify(data, null, 2),
                            'utf-8'
                        );
                    }
                } else {
                    console.log(`      ✅ 200 OK - ${contentType}`);
                }
            } else {
                console.log(`      ❌ ${response.status()}`);
            }
        } catch (error) {
            console.log(`      ❌ Error: ${error.message.substring(0, 60)}`);
        }
    }
    
    await browser.close();
}

async function main() {
    console.log('\n' + '='.repeat(80));
    console.log('öffentlichevergabe.de API-ZUGRIFF');
    console.log('='.repeat(80));
    console.log(new Date().toISOString());
    
    // Schritt 1: Swagger-Spec extrahieren
    const spec = await extractSwaggerSpec();
    
    // Schritt 2: API-Calls testen
    if (spec && spec.paths) {
        await testDirectAPICall(spec);
    }
    
    console.log('\n' + '='.repeat(80));
    console.log('FERTIG!');
    console.log('='.repeat(80));
    console.log('\nDateien:');
    console.log('   • swagger_spec.json - Vollständige API-Spezifikation');
    console.log('   • swagger_ui.png - Screenshot der Swagger-UI');
    console.log('   • sample_*.json - Beispiel-Responses (falls erfolgreich)');
    console.log('\n');
}

main().catch(console.error);
