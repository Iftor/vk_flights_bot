# VK bot for booking flight tickets (v1.0)

## Installing
```pip install -r requirements.txt```

## Preparing
Create file ```settings.py``` and put there:
1. ```GROUP_ID``` with ID of your VK group;
2. ```TOKEN``` with token of your VK bot;
3. ```DB_CONFIG``` with DB settings like this:
```
DB_CONFIG = {
    'provider': 'some db provider',
    'user': 'some username',
    'password': 'some password',
    'host': 'some hostname',
    'database': 'some db name'
}
```

## Running
```python bot.py```

##Note
In ```flights.py``` implements random generation of flights. You can connect the API to get real flights