from util.logging import get_logger
from server.sync.onchain import w3
import time

logger = get_logger()

def wait_for_blocks(blocks=10):
    initial_block_number = w3.eth.block_number

    while True:
        current_block_number = w3.eth.block_number
        if current_block_number >= initial_block_number + blocks:
            break
        logger.info(f"Waiting for blocks... Current: {current_block_number - initial_block_number}, Required: {blocks}")
        time.sleep(5)  # Wait for 5 seconds before checking again
