from web3 import Web3

CONTRACT_ADDRESS = "0xf8e81D47203A594245E36C48e151709F0C19fBe8"

ABI = [
    {
        "inputs": [
            {"internalType": "string","name": "_hash","type": "string"},
            {"internalType": "string","name": "_owner","type": "string"}
        ],
        "name": "registerImage",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string","name": "","type": "string"}],
        "name": "images",
        "outputs": [
            {"internalType": "string","name": "hash","type": "string"},
            {"internalType": "string","name": "owner","type": "string"},
            {"internalType": "uint256","name": "timestamp","type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string","name": "_hash","type": "string"}],
        "name": "verifyImage",
        "outputs": [
            {"internalType": "string","name": "","type": "string"},
            {"internalType": "uint256","name": "","type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_contract():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

    if not w3.is_connected():
        raise Exception("Không kết nối được Ganache")

    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
    account = w3.eth.accounts[0]

    return w3, contract, account

def register_on_chain(image_hash, owner):
    try:
        w3, contract, account = get_contract()

        tx_hash = contract.functions.registerImage(
            image_hash,
            owner
        ).transact({"from": account})

        w3.eth.wait_for_transaction_receipt(tx_hash)

        print("✅ Đã ghi lên blockchain")
        return True

    except Exception as e:
        print("❌ Lỗi blockchain:", e)
        return False

def verify_on_chain(image_hash):
    try:
        w3, contract, _ = get_contract()

        owner, timestamp = contract.functions.verifyImage(image_hash).call()

        return {
            "valid": True,
            "owner": owner,
            "timestamp": timestamp
        }

    except Exception as e:
        print("❌ Verify lỗi:", e)
        return {"valid": False}