# Cinema Reservation System

## Description

This project simulates a cinema reservation system using Apache Cassandra as the database. The system includes functionalities to create screenings, make and update reservations, and perform stress tests to evaluate the system's performance under high load.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_directory>

2. **Create new volume, copy setup and execute it (optionally check it):**:
   ```bash
   docker-compose up -d
   docker cp setup.cql cassandra-node1:/setup.cql
   docker exec -it cassandra-node1 cqlsh -f /setup.cql
   docker exec -it cassandra-node1 cqlsh


## Database Schema

The database schema for the Cinema Reservation System consists of three main tables: `rooms`, `screenings`, and `reservations`.

- **rooms:**
  This table stores information about the different rooms available in the cinema.
  - `room_id` (UUID): Primary key, unique identifier for each room.
  - `name` (TEXT): Name of the room.
  - `num_seats` (INT): Number of seats in the room.

- **screenings:**
  This table stores information about the different screenings available in the cinema.
  - `screening_id` (UUID): Unique identifier for each screening.
  - `room_id` (UUID): Foreign key referencing the `rooms` table.
  - `screening_time` (TIMESTAMP): Time of the screening.
  - Primary Key: (`room_id`, `screening_time`)

- **reservations:**
  This table stores information about the reservations made by users.
  - `reservation_id` (UUID): Primary key, unique identifier for each reservation.
  - `user_id` (UUID): Unique identifier for each user.
  - `screening_id` (UUID): Foreign key referencing the `screenings` table.
  - `seat_number` (INT): Seat number for the reservation.
  - `reservation_time` (TIMESTAMP): Time when the reservation was made.
  - Primary Key: (`screening_id`, `seat_number`)

Indexes:
  - An index on `reservation_id` in the `reservations` table for quick lookup by reservation ID.
  - An index on `name` in the `rooms` table for quick lookup by room name.

This schema ensures efficient management and querying of rooms, screenings, and reservations in the cinema reservation system.

## Python Scripts

### main.py
This script contains the core functionalities for managing the cinema reservation system. It includes functions to create screenings, make reservations, update reservations, and view available seats.

- **Functions:**
  - `get_session()`: Establishes a connection to the Cassandra database.
  - `create_screenings(session)`: Creates screenings for all rooms.
  - `make_reservation(session, user_id, room_name, date, time, seat_number, reservation_counts)`: Makes a reservation for a given user.
  - `update_reservation(session, reservation_id, new_seat_number)`: Updates an existing reservation to a new seat number.
  - `view_reservation(session, reservation_id)`: Displays details of a reservation by its ID.
  - `view_available_seats(session, room_name, date, time)`: Lists available seats for a given screening.
  - `main()`: Main function to interact with the user via command-line inputs.

### manage_data.py
This script provides a command-line interface to manage and view reservations and screenings. It includes options to show all reservations, delete all reservations, delete all screenings and related reservations, show all screenings, and show the number of reservations made by a given client.

- **Functions:**
  - `get_session()`: Establishes a connection to the Cassandra database.
  - `show_all_reservations(session)`: Displays all reservations.
  - `delete_all_reservations(session)`: Deletes all reservations.
  - `delete_all_screenings_and_related_data(session)`: Deletes all screenings and related reservations.
  - `show_all_screenings(session)`: Displays all screenings.
  - `show_reservation_count(session)`: Shows the total number of reservations.
  - `show_reservation_count_by_client(session, user_id)`: Shows the number of reservations made by a specific client.
  - `main()`: Main function to interact with the user via command-line inputs.

### stress_tests.py
This script is designed to perform stress tests on the cinema reservation system to evaluate its performance under high load. It includes three different stress tests.

- **Functions:**
  - `stress_test1(session, number_of_actions)`: Simulates a single client making the same reservation request repeatedly.
  - `stress_test2(session, repetitions, num_clients)`: Simulates multiple clients making random reservation requests.
  - `stress_test_3(session, num_clients, screening_details)`: Simulates immediate occupancy of all seats by multiple clients.
  - `client_task(session, user_id, repetitions)`: Task for each client in stress test 2 to make random reservations or updates.
  - `reserve_max(session, user_id, screening_details, reserved_seats)`: Task for each client in stress test 3 to make maximum reservations.
  - `main()`: Main function to choose and run the desired stress test, and measure the time taken for execution.

## Results and Error Handling

### Error Handling
- **Database Connection:**
  - The `get_session` function establishes a connection to the Cassandra database. If the connection fails, the error is propagated, and appropriate messages are logged.

- **Reservation and Screening Operations:**
  - **Making Reservations:**
    - If a reservation fails (e.g., due to a seat being already occupied), an error message is printed, and the function returns `False`.
  - **Updating Reservations:**
    - The update operation first checks if the reservation exists and if the new seat is available. If these conditions are not met, appropriate error messages are printed, and the function returns `False`.
    - If the update operation fails during execution, an error message is printed, and the function returns `False`.

- **Command-line Interface (CLI) Operations:**
  - **Invalid Inputs:**
    - The CLI functions in `main.py` and `manage_data.py` handle invalid inputs by printing error messages and prompting the user to try again.
  - **Database Operations:**
    - Each database operation is wrapped in try-except blocks to catch and log any exceptions that occur, ensuring that the program does not crash unexpectedly.

### Results
- **Stress Test 2 & 3:**
  - Both tests took approximately 120 seconds to complete on a 10-year-old laptop.

## Problems Encountered

### 1. Data Consistency Errors
- **Problem:** During the initial testing phase, there were instances where the data was not consistent across different nodes in the Cassandra cluster, leading to inaccurate query results.
- **Solution:** Set the consistency level to `ConsistencyLevel.ALL` for critical operations to ensure data consistency across all nodes. This change improved the reliability of the data.

### 2. Allow Filtering Issues
- **Problem:** Some queries required the use of `ALLOW FILTERING`, which can lead to performance unpredictability and potential issues with large datasets.
- **Solution:** Revised the database schema to include additional indexing and designed queries to avoid the need for `ALLOW FILTERING`. This approach improved query performance and stability.

### 3. Handling Large Volume of Data
- **Problem:** Managing and processing the large volume of reservation data generated during stress tests was challenging, especially in terms of cleanup and ensuring no residual data affected subsequent tests.
- **Solution:** Developed efficient data cleanup procedures and automated the deletion of all screenings and related reservations after each stress test. This maintained a clean state for each test run.

### 4. Error Handling and Logging
- **Problem:** Initial implementations lacked comprehensive error handling and logging, making it difficult to diagnose and fix issues.
- **Solution:** Enhanced error handling by adding detailed try-except blocks around critical operations and implemented logging to capture and record errors and system states. This improved the debugging process and system reliability.

### 5. Integration and Compatibility Issues
- **Problem:** Integration of different modules (main.py, manage_data.py, stress_tests.py) initially faced compatibility issues, such as conflicting data structures and inconsistent function interfaces.
- **Solution:** Standardized the function interfaces and data structures across all modules, ensuring seamless integration. Regular integration testing was conducted to identify and resolve issues promptly.
