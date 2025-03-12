import time
import os
import asyncio
from aiohttp import ClientSession, TCPConnector, AsyncResolver
from web3 import Web3
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator
from eth_account import Account
from colorama import Fore, Back, Style, init

# Инициализация Colorama
init()

# Подключение к твоей легкой ноде
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # Укажи адрес своей ноды

# Функция для генерации сид-фразы
def generate_seed_phrase():
    entropy = os.urandom(16)  # Генерация 128 бит энтропии
    mnemonic = Bip39MnemonicGenerator().FromEntropy(entropy_bytes=entropy)
    return mnemonic

# Асинхронная функция для проверки баланса кошелька
async def check_wallet_balance(session, mnemonic):
    seed = Bip39SeedGenerator(mnemonic).Generate()
    account = Account.from_key(seed[:32])  # Первые 32 байта seed как приватный ключ
    address = account.address

    try:
        async with session.post(w3.provider.endpoint_uri, json={
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }) as response:
            data = await response.json()
            balance = int(data['result'], 16)
            return mnemonic, address, balance  # Возвращаем мнемонику
    except Exception as e:
        print(Fore.RED + f"Ошибка при получении баланса для адреса {address}: {e}" + Style.RESET_ALL)
        return mnemonic, address, None  # Возвращаем None в качестве баланса

# Функции для сохранения кошельков в файлы
def save_wallet_to_file(mnemonic, address, balance, filename="wallets_with_balance.txt"):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"Сид-фраза: {mnemonic}\n")
        file.write(f"Адрес: {address}\n")
        file.write(f"Баланс: {balance} Wei\n\n")

def save_empty_wallet_to_file(mnemonic, filename="wallets_empty.txt"):
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{mnemonic}\n")  # Сохраняем только мнемоническую фразу

# Основная асинхронная функция (теперь бесконечная)
async def generate_and_check_seed_phrases():
    total_generated = 0
    wallets_with_balance = 0
    start_time = time.time()  # Записываем начальное время

    # Используем кастомный DNS-резолвер (Google DNS)
    resolver = AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4", "1.1.1.1"])
    connector = TCPConnector(resolver=resolver)

    async with ClientSession(connector=connector) as session:
        while True:  # Бесконечный цикл
            mnemonic = generate_seed_phrase()
            mnemonic, address, balance = await check_wallet_balance(session, mnemonic)  # Получаем мнемонику
            total_generated += 1

            if balance is not None and balance > 0:  # Проверяем, что баланс не None
                wallets_with_balance += 1
                save_wallet_to_file(mnemonic, address, balance)
                elapsed_time = time.time() - start_time
                speed = total_generated / elapsed_time
                print(Fore.GREEN + f"Всего создано: {total_generated} | С балансом: {wallets_with_balance} | Скорость: {speed:.2f} кошельков/сек | " +
                      Fore.CYAN + f"Найден кошелек с балансом! Сид-фраза: {mnemonic}, Адрес: {address}, Баланс: {balance} Wei" + Style.RESET_ALL)
            else:
                elapsed_time = time.time() - start_time
                speed = total_generated / elapsed_time
                save_empty_wallet_to_file(mnemonic)  # Передаем только мнемонику
                print(Fore.YELLOW + f"Всего создано: {total_generated} | С балансом: {wallets_with_balance} | Скорость: {speed:.2f} кошельков/сек | " +
                      Fore.WHITE + f"Кошелек существует, но баланс равен нулю. Сид-фраза: {mnemonic}, Адрес: {address}" + Style.RESET_ALL)

            # Вывод статистики каждые 1000 сгенерированных кошельков
            if total_generated % 1000 == 0:
                elapsed_time = time.time() - start_time
                speed = total_generated / elapsed_time
                print(Back.BLUE + Fore.WHITE + "\n--- Статистика (каждые 1000 кошельков) ---" + Style.RESET_ALL)
                print(Fore.BLUE + f"Всего сгенерировано сид-фраз: {total_generated}" + Style.RESET_ALL)
                print(Fore.BLUE + f"Кошельков с балансом: {wallets_with_balance}" + Style.RESET_ALL)
                print(Fore.BLUE + f"Скорость: {speed:.2f} кошельков/сек" + Style.RESET_ALL)
                print(Fore.BLUE + f"Сохраненные кошельки с балансом записаны в файл 'wallets_with_balance.txt'" + Style.RESET_ALL)
                print(Fore.BLUE + f"Сохраненные мнемонические фразы пустых кошельков записаны в файл 'wallets_empty.txt'" + Style.RESET_ALL)

# Запуск асинхронной генерации и проверки
if __name__ == "__main__":
    if os.name == 'nt':
        from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(generate_and_check_seed_phrases())  # Запуск без аргументов для бесконечной генерации

