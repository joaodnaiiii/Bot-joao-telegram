import asyncio
from src.bots.shop_bot import bot as shop_bot, router as shop_router, init_db as init_db_shop
from src.bots.admin_bot import bot as admin_bot, router as admin_router, init_db as init_db_admin


async def main():
    await init_db_shop()
    await init_db_admin()
    await asyncio.gather(
        shop_router.start_polling(shop_bot),
        admin_router.start_polling(admin_bot),
    )


if __name__ == "__main__":
    asyncio.run(main())