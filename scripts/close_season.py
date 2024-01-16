from brownie.network import accounts
from brownie import ArcModel

from scripts.util import (
    contract_from_address,
    get_package,
    from_block,
    s2b
)

MIN_RISK_CLOSING_BALANCE = 10**17
MIN_POLICY_PROCESSING_BALANCE = 10**17


def process_policies(mapper, product, policies_offset=0, count=10**6, set_gas_price=False):

    owner = accounts.at(product.getOwner())

    gif = get_package('gif-contracts')
    registry = contract_from_address(gif.RegistryController, product.getRegistry())
    instance_service = contract_from_address(gif.InstanceService, registry.getContract(s2b('InstanceService')))

    policies_count = mapper.ids()
    if count < policies_count:
        policies_count = count

    for idx in range(policies_offset, policies_count):
        policy_id = mapper.getId(idx)
        process_id = mapper.getProcessId(policy_id)
        policy = instance_service.getPolicy(process_id).dict()

        payouts = instance_service.payouts(process_id)
        if payouts >= 1:
            print(f"{idx+1}/{policies_count} process_id {process_id} payouts {payouts}. already processed. skipping ...")
        elif instance_service.claims(process_id) >= 1:
            print(f"{idx+1}/{policies_count} process_id {process_id}. CHECK!!! payouts = 0, claims > 0 skipping ...")
        else:
            owner_balance = owner.balance()
            print(f"{idx+1}/{policies_count} process_id {process_id}. owner balance {owner_balance/10**18:.2f} processing ...")

            if owner_balance < MIN_POLICY_PROCESSING_BALANCE:
                print(f"owner balance too low. re-fund owner. exiting...")
                return

            product.processPolicy(
                process_id,
                from_block(owner, set_gas_price=set_gas_price))


def finalize_risks(product, risk_offset=0, count=10**6, set_gas_price=False):

    owner = accounts.at(product.getOwner())
    model = contract_from_address(ArcModel, product.getModel())

    if model.owner() != product.getOwner():
        print(f"attempt to transfer model owner to {owner}. exiting ...")
        product.transferModel(
            owner, 
            from_block(owner, set_gas_price=set_gas_price))

        # exit in case transfer failed
        if model.owner() != owner:
            print(f"failed to transfer model owner {model.owner()}. exiting ...")
            return

    risk_count = model.risks()
    if count < risk_count:
        risk_count = count

    for idx in range(risk_offset, risk_count):
        risk_id = model.getRiskId(idx)
        risk = model.getRisk(risk_id).dict()
        is_final = risk['isFinal']

        if is_final:
            print(f"{idx+1}/{risk_count} is_final {is_final}. already final. skipping ...")
        else:
            owner_balance = owner.balance()
            print(f"{idx+1}/{risk_count} is_final {is_final}. owner balance {owner_balance/10**18:.2f} processing ...")

            if owner_balance < MIN_RISK_CLOSING_BALANCE:
                print(f"owner balance too low. re-fund owner. exiting...")
                return

            model.setRisk(
                risk_id, 
                True, 
                True, 
                from_block(owner, set_gas_price=set_gas_price))


