import asyncio
from typing import Union
from playwright.async_api import async_playwright


async def get_element_content(url: str, xpath: str, semaphore: asyncio.Semaphore) -> Union[str, None]:
    """
    Асинхронно извлекает содержимое элемента с указанной страницы по XPath.

    :param url: URL страницы с товаром.
    :param xpath: XPath для элемента, содержащего цену.
    :param semaphore: Семафор для ограничения количества параллельных запросов.
    :return: Цена в виде строки или сообщение об ошибке.
    """
    async with semaphore:  # Ждем, если лимит запросов превышен
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ru-RU',
                timezone_id='Europe/Moscow'
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = await context.new_page()
            await page.set_extra_http_headers({
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            })

            await page.goto(url, wait_until='domcontentloaded')

            try:
                element = await page.wait_for_selector(f'xpath={xpath}', timeout=20000)
                content = await element.text_content()
                await browser.close()
                return content
            except Exception as e:
                await browser.close()
                return str(e)
