# Etherisc Platform for eSusFarm

## Etherisc Data Architecture

### Model Definition

The diagram below shows the layout for entities with their attributes.

```mermaid
classDiagram

    class Entity {
        On-chain Attributes
        Off-chain Attributes ()
    }
```

On-chain attributes are located in the upper part of the box and can be read by anybody.

Off-chain attributes are located in the lower part of the box and are only stored in classical IT systems. 
These attributes are considered private data and can only be read by people that have the necessary authorization.

### Data Model Overview

```mermaid
classDiagram

    Policy --o Person
    Policy --o Risk
    Policy --* Payout
    Risk --o Config
    Risk --o Location

    class Person {
        ID ()
        First Name ()
        Last Name ()
        Gender ()
    }

    class Policy {
        ID
        Person ID ()
        Risk ID
        Subscription date
        Sum Insured amount
        Premium amount
    }

    class Payout {
        Payout amount
        Execution date
    }

    class Risk {
        ID
        Config ID
        Location ID
        Crop
        Deductible
        Draught Loss
        Excess Rainfall Loss
        Total Loss
        Payout
        Final Payout
    }

    class Config {
        ID
        Year
        Region
        Start of season
        End of season
        Franchise
        Client () do we need this?
    }

    class Location {
        ID
        Region ()
        District ()
        Subcounty ()
        Latitude ()
        Longitude ()
    }
```


## Data Flow

The product definition data below is shared before the beginning of the season

* INPUT Location
* INPUT Config
* INPUT Risk (with deductible, without loss and payout values)

The onboarding data below is shared during the beginning of the season

* INPUT Person
* INPUT Policy

The data below is shared at the end of season (as soon as loss/payout data becomes available)

* INPUT Risk (loss and payout values)

At the end of the season the Etherisc platform provides the following data

* OUTPUT Payout data per policy


## API Details

example values taken from https://public.tableau.com/app/profile/parametric.solutions/viz/Index_Monitoring_Maize_2023_B_Uganda/IndexMonitroing

### Location API (Example)

```
POST /api/v1/location
```

Request Body 
```json
{
    "id": "345abc",
    "region": "Northern",
    "district": "AGAGO",
    "subcounty": "Wol",
    "latitude": 3.198,
    "longitude": 33.111
}
```

Data field comments:

* `id`: Existing system ID or value derived from it

Validations:

* id: not null, unique
* region: element of fixed set of regions
* district: element of fixed set of districts
* subcounty: not null, unique
* latitude: float value within country bounding box
* longitude: float value within country bounding box

### Config API (Example)

```
POST /api/v1/config
```

Request Body 
```json
{
    "id": "234abc",
    "region": "Northern",
    "start_of_season": "2024-03-21",
    "end_of_season": "2024-07-28",
    "franchise": 0.1
}
```

Data field comments:

* `id`: Existing system ID or value derived from it

Validations:

* id: not null, unique
* region: element of fixed set of regions
* start of season: >= 2024, valid iso date
* end of season: within meaningful range given start data
* franchise: float, within meaningful range

### Risk API (Example)

```
POST /api/v1/risk
```

Request Body 
```json
{
    "id": "123abc",
    "config_id": "234abc",
    "location_id": "345abc",
    "crop": "Maize",
    "deductible": 0.1
}
```

Data field comments:

* `id`: Existing system ID or value derived from it

Validations:

* id: not null, unique
* config_id: existing config
* location_id: existing location
* crop: element of fixed set of crops
* deductible: float, within meaningful range

Endpoint to provide end of season data

```
PUT /api/v1/risk/risk_id
```

Request Body 
```json
{
    "drought_loss": 0.32,
    "excess_rainfall_loss": 0.18,
    "total_loss": 0.34,
}
```

Validations:

* risk id: existing risk id
* drought loss: float, within meaningufl range
* excess rainfall loss: float, within meaningufl range
* total loss: to be defined (can this be derived from the above values?)

### Person API (Example)

```
POST /api/v1/person
```

Request Body 
```json
{
    "id": "333abc",
    "first_name": "Yentabpoa",
    "last_name": "Bokoum",
    "gender": "F",
}
```

Data field comments:

* `id`: Existing system ID or value derived from it

Validations:

* id: not null, unique
* gender: null or regexp


### Policy API (Example)

Things to define/questios
* Dealing with application states. Assumption is we don't need this for the MVP
* Multiple policies per person. Assumption is we have one policy per person for the MVP
* Link between sum insured and premium. To be calculated in smart contract (eg via ratio in risk)?

```
POST /api/v1/policy
```

Request Body 
```json
{
    "id": "765abc",
    "person_id": "333abc",
    "risk_id": "123abc",
    "subscription": "2024-02-15",
    "sum_insured": 200000,
    "premium": 20000,
}
```

Data field comments:

* `id`: Existing system ID or value derived from it

Validations:

* id: not null, unique
* person id: person existing
* risk id: risk existing
* subscription: to be defined
* sum insured: float, meaningful range (tbd)
* premium: float, meaningful range

    class Policy {
        ID
        Person ID ()
        Risk ID
        Subscription date
        Sum Insured amount
        Premium amount
    }

## Python Setup

After a devcontainer rebuild you might need to uninstall/reinstall the right python packages first

You have to cd first as two incompatible `requirements.txt` are needed

### Apple Silicon

Install rosetta 2 first

```bash
/usr/sbin/softwareupdate --install-rosetta --agree-to-license
```

Rebulid container 

### Brownie Setup

Inside devocontainer shell install brownie and compile contracts

```bash
pip install eth-brownie
brownie console
```

in console
```python
def frm(account):
    # priority fee attribute required when working with anvii
    return {'from':account, 'priority_fee': '2 gwei'}

cnt = Counter.deploy(frm(accounts[0]))
cnt.setValue(42, frm(accounts[0]))
cnt.value()
```

### Step by Step

```bash
# you have to cd first as two incompatible requirements.txt are needed
cd scripts
# or here
cd app

pip freeze > uninstall.txt
pip uninstall -y -r uninstall.txt
pip install -r requirements.txt
rm uninstall.txt
```

Check Brownie Console (Anvil)
```bash
touch /home/vscode/.brownie/packages/etherisc/gif-interface@2.0.0-rc.1/.env
touch /home/vscode/.brownie/packages/etherisc/gif-contracts@2.0.0-rc.1-chainlink.1.3.13/.env
brownie console
```

```python
xof = EXOF.deploy({'from': accounts[0], 'gas_price': web3.eth.gas_price})
xof.symbol()
```

Deploy Setup on local Anvil
```python
from scripts.deploy import help
help()
```

## Finalize Season

1. Transfer model owner back to product_owner
1. Finalize risk
1. Process policy

```python
product.transferModel(product.getOwner(), {'from': product.getOwner(). 'gas_price': web3.eth.gas_price})
model.setRisk(risk_id, True, True, {'from': model.owner(), 'gas_price': web3.eth.gas_price})
product.processPolicy(policy_id, {'from': product.getOwner(), 'gas_price': web3.eth.gas_price})
```


## Work with Polygon Mainnet
Add polygon to brownie networks and start console using it.

Set the alchemy project id in the .env file in the project root.
```
WEB3_ALCHEMY_PROJECT_ID=X...
```

```bash
brownie networks import polygon-network.yaml
brownie console --network=polygon-alchemy
```



## Upload Data

```bash
cd upload_data
python
```

Current state
```python
from read_pam import load
data = load()

#  check 1st row of pam excel
data['Reporting PAM'][2]
```

## Running the API Server Locally

```bash
cd app
python3 main.py
```

Open the browser at `http://localhost:8000`. 
The actual port is shown in the ports tab of VSCode.

## Initial Dokku Setup

```
# create dokku application 
dokku apps:create wfp-api

# add new domain and remove default domain
dokku domains:add wfp-api api.wfp.etherisc.com
dokku domains:remove wfp-api wfp-api.wfp.etherisc.com

# set correct proxy ports for http and https
dokku ports:add wfp-api https:443:8000
dokku ports:add wfp-api http:80:8000

# create mongo service
dokku mongo:create mongo-wfp-api

# link the mongo service to the app
dokku mongo:link mongo-wfp-api wfp-api

# now push deployment via git 
# 1. add new git remote 'git remote add dokku dokku@<host>:wfp-api'
# 2. 'git push dokku master:main'

# enable let's encrypt for https certificates
dokku letsencrypt:enable wfp-api

# app should be ready now - open in browser
```

## Dokku Deploy new version

### Deploy

On local machine
```bash
git push dokku master:main
```

Check update in browser `https://api.wfp.etherisc.com/docs`

### Check MongoDB

Open SSH tunnel to access MongoDB (assuming it is exposed on 29378)
```
ssh -L 27017:localhost:29378 matthias@162.55.209.69
```

Verify that MongoDB is exposed under the expected port
```
dokku mongo:info mongo-wfp-api
```
Browse the database using MongoDB Compass 

### Check/Fix Things

Switch to remote server
```bash
ssh matthias@162.55.209.69
```

On remote server
```bash
# show all apps (should have wfp-api in its list)
dokku apps:list
# show log
dokku logs wfp-api
# show defined env variables
dokku config wfp-api
# set/adapt env variables
dokku config:set wfp-api MAPPER_ADDRESS=0x9C0F71971BA7768EADD2421d9Cf2CF9ADA326B84
```


### Dokku mongo debug connection

Example using service _mongo-wfp-api_:

1. Expose mongo port on dokku `dokku mongo:expose mongo-wfp-api`
1. Find the exposed port in the output above or via `dokku mongo:info mongo-wfp-api`

```
dokku mongo:info mongo-wfp-api | grep 'Exposed ports:' | sed 's/[[:space:]]\+/ /g' | cut -d' ' -f4 | cut -d'>' -f2
```

1. Open ssh tunnel with dokku mongo port forward `ssh -L <remote-port>:localhost:27017 user@host` (format <remote-port:local-host:local-port>)
1. Now connect with mongo client of choice using `localhost:6479` as host and the password mentioned in mongo info
1. When finished, close the ssh tunnel by logging out of the ssh shell and unexpose the mongo port `dokku mongo:unexpose mongo-wfp-api`
