
Some scripts to help with Load Testing, especially useful for finding
errors with database pools and that kind of thing.

Requires the Locust.io module from http://locust.io/

    pip install locustio

Run with:

    locust -f one_question.py --host=http://localhost:8080
    
And go to http://localhost:8089/  in web browser to start/control the load test.