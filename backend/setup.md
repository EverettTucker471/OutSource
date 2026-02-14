I want to create a python backend for my mobile app. It will need to use a MySQL DB. We want to use docker for running the app and the DB.

Please do the following:
1. create boilerplate code for the app. include a controller, service, and repository layer for each entity along with DTOs. start with a user, which should be created and has the following information:
{
    id: long (unique)
    username: string (unique)
    password: string (this will store a hash)
    name: string
    friends: list<long>
    groups: list<long>
}
make sure you have a basic API endpoints to post a user with POST /users,  get the current user with /users/current, and get a specific user by id with GET /users/{id}
2. create a mysql db to store a table of users
3. create dockerfiles to run these in containers
4. test that these run
5. create an "instructions.md" file to explain how to run each docker container
