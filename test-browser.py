"""Optional reproducibility check: Python + Playwright + Chromium. No tools needed to use site."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
import os, shutil
root=Path(__file__).resolve().parent
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root.parent)))
Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/{root.name}/index.html'
try:
 with sync_playwright() as p:
    executable=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
    b=p.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1440,'height':1000}); errors=[]; external=[]
    pg.on('pageerror',lambda e: errors.append(str(e)))
    pg.on('request',lambda r:external.append(r.url) if not r.url.startswith(f'http://127.0.0.1:{server.server_port}/') else None)
    if os.environ.get('TEST_HTTP')=='1':
      assert pg.goto(url).status==200
    else:
      pg.set_content((root/'index.html').read_text(encoding='utf-8'))
    assert pg.locator('#calc-threshold').inner_text()=='148 шт.'
    assert '40\xa0800' in pg.locator('#calc-results').inner_text().replace('\u202f','\xa0')
    assert '57\xa0800' in pg.locator('#calc-results').inner_text().replace('\u202f','\xa0')
    assert 'только в части' in pg.locator('#calc-message').inner_text()
    assert pg.locator('.hero-visual img').evaluate('(el)=>el.complete&&el.naturalWidth>0')
    # The interactive home example shares the same economic core.
    assert pg.locator('#demo-income').inner_text().replace('\u202f',' ').replace('\xa0',' ')=='44 200 ₽'
    slider=pg.locator('#demo-sales');slider.focus();slider.press('Home')
    assert 'При том же' in pg.locator('#demo-message').inner_text()
    slider.fill('147');assert pg.locator('#demo-delta').inner_text().startswith('−');assert 'доход снизился' in pg.locator('#demo-message').inner_text()
    slider.press('ArrowRight');assert slider.input_value()=='148';assert 'Цель достигнута' in pg.locator('#demo-message').inner_text()
    assert pg.locator('#demo-income').inner_text().replace('\u202f',' ').replace('\xa0',' ')=='50 320 ₽'
    slider.press('End');assert slider.input_value()=='190';assert pg.locator('#demo-income').inner_text().replace('\u202f',' ').replace('\xa0',' ')=='64 600 ₽'
    slider.fill('130')
    print('Интерактивный пример: 100, 130, 147, 148 и 190 продаж, управление клавиатурой – OK')
    if os.environ.get('CAPTURE'): pg.screenshot(path=os.environ['CAPTURE'])
    assert pg.locator('#home').is_visible() and not pg.locator('#training').is_visible()
    pg.locator('nav a[href="#calculator"]').click(); pg.locator('#calculator').wait_for(state='visible'); assert pg.locator('#calculator').is_visible() and not pg.locator('#home').is_visible()
    assert pg.locator('nav a[href="#calculator"]').get_attribute('aria-current')=='page'
    # calculator boundary, invalid, stock, missing demand and reset
    pg.locator('#stock').fill('140'); assert 'запас' in pg.locator('#calc-message').inner_text()
    pg.locator('#stock').fill('200');pg.locator('#unknown').check(); assert pg.locator('#lo').is_disabled();assert 'нужен диапазон' in pg.locator('#calc-message').inner_text()
    pg.locator('#unknown').uncheck();pg.locator('#lo').fill('190');assert 'Проверьте' in pg.locator('#calc-results').inner_text()
    pg.locator('#lo').fill('148');pg.locator('#hi').fill('148');assert 'во всех' in pg.locator('#calc-message').inner_text()
    pg.locator('#p1').fill('1375');assert 'неположителен' in pg.locator('#calc-message').inner_text()
    pg.locator('#p1').fill('1000');assert pg.locator('.chart-axis .signed.neg').count()==2;assert 'Отрицательные значения' in pg.locator('.chart-legend').inner_text()
    pg.locator('#p1').fill('');assert 'Проверьте' in pg.locator('#calc-results').inner_text()
    pg.locator('#calc-form button[type=reset]').click();pg.wait_for_function("document.getElementById('calc-threshold')?.textContent==='148 шт.'")
    print('Калькулятор: исходный сценарий, запасы, неизвестный спрос, неверный диапазон, равенство порогу, нулевая маржа, пустые поля, сброс – OK')
    pg.locator('nav a[href="#training"]').click();pg.locator('#training').wait_for(state='visible');assert pg.locator('#training').is_visible()
    pg.locator('input[name=ans][value=below]').check()
    pg.locator('nav a[href="#method"]').click();pg.locator('#method').wait_for(state='visible')
    pg.locator('#sources summary').click();assert pg.locator('#sources .source-list').is_visible()
    pg.locator('nav a[href="#training"]').click();pg.locator('#training').wait_for(state='visible')
    assert pg.locator('input[name=ans][value=below]').is_checked()
    assert pg.locator('#submit').is_enabled()
    pg.locator('#restart').click();assert pg.locator('#submit').is_disabled()
    print('Навигация: переходы между разделами, сохранение ответа, раскрытие источников – OK')
    paths=[(['below','cross','above','missing','above','no','no','yes','yes','cross','below','missing','yes'],True,'6 из 6'),(['above','above','below','above','below','yes','yes','no','no','above','above','above','no'],False,'0 из 6')]
    for choices,correct,score in paths:
      for i,a in enumerate(choices):
        assert pg.locator('#submit').is_disabled(); assert pg.locator('#training-theory').is_visible()==(i<9); pg.locator(f'input[name=ans][value={a}]').check()
        if i in [3,11]: pg.locator(f'input[name=detail][value={"range" if correct else "logo"}]').check()
        if i==9:pg.locator('#threshold').fill('105' if correct else '1')
        assert pg.locator('#submit').is_enabled();pg.locator('#submit').click();assert pg.locator('input[name=ans]').first.is_disabled()
        if i>=9:
          assert pg.locator('#feedback').inner_text()=='Ответ сохранен. Разбор будет доступен после всех заданий'
          assert pg.locator('.choice.is-correct,.choice.is-incorrect').count()==0
        else:
          assert pg.locator('.choice.is-correct').count()>=1
          assert pg.locator('.feedback.good').count()==int(correct)
        pg.locator('#next').click()
      assert pg.locator('.score').inner_text()==score
      assert pg.locator('.review').count()==4
      pg.locator('.review summary').first.click()
      assert pg.locator('.review .answer-picked').first.is_visible()
      pg.locator('#restart').click();assert 'Учебное задание 1 из 9' in pg.locator('#step').inner_text()
    print('Тренажер: 13 заданий; полные правильный и неправильный маршруты (6/6 и 0/6); блокировка, отложенная обратная связь, сброс – OK')
    for width in [320,390,768,1440]:
      pg.set_viewport_size({'width':width,'height':900})
      for page in ['home','training','calculator','method','about']:
        pg.locator(f'nav a[href="#{page}"]').click();pg.wait_for_timeout(100)
        assert pg.locator('#'+page).is_visible() and pg.locator('[data-view]:visible').count()==1
        assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'overflow {width} {page}'
      assert pg.locator('#about').inner_text().find('ChatGPT')>=0
    pg.locator('nav a[href="#home"]').click()
    pg.locator('#home').wait_for(state='visible')
    if os.environ.get('CAPTURE'): pg.screenshot(path=os.environ['CAPTURE'],full_page=True)
    print('Адаптивность: пять экранов на 320, 390, 768 и 1440 px; горизонтального переполнения нет – OK')
    assert not errors,errors;assert not external,external
    print('Логотип, отсутствие ошибок JS и внешних запросов при проверенных действиях – OK')
    print('Режим: HTTP' if os.environ.get('TEST_HTTP')=='1' else 'Режим: загрузка точного содержимого index.html (set_content)')
    b.close()
finally:server.shutdown()
