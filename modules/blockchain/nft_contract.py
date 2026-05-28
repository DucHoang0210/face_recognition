from web3 import Web3
import os

NFT_RPC_URL = os.getenv('NFT_RPC_URL', 'http://127.0.0.1:8545')
NFT_CONTRACT_ADDRESS = os.getenv('NFT_CONTRACT_ADDRESS', '0x5FbDB2315678afecb367f032d93F642f64180aa3')

NFT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "tokenURI", "type": "string"}
        ],
        "name": "mint",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "mintFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def get_nft_contract():
    w3 = Web3(Web3.HTTPProvider(NFT_RPC_URL))
    if not w3.is_connected():
        raise Exception(f"Không kết nối được node NFT tại {NFT_RPC_URL}")

    contract = w3.eth.contract(address=Web3.to_checksum_address(NFT_CONTRACT_ADDRESS), abi=NFT_ABI)
    return w3, contract


def get_mint_fee():
    w3, contract = get_nft_contract()
    return contract.functions.mintFee().call()


def mint_nft(token_uri: str, value_wei: int | None = None):
    w3, contract = get_nft_contract()
    account = w3.eth.accounts[0]

    if value_wei is None:
        value_wei = contract.functions.mintFee().call()

    tx_hash = contract.functions.mint(token_uri).transact({
        "from": account,
        "value": value_wei,
    })

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt
