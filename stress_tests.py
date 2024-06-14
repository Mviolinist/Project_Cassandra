import sys
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from main import get_session, create_screenings, make_reservation, update_reservation
from manage_data import delete_all_screenings_and_related_data
import random
import threading

R = 7   # number of rooms = R
S = 7   # number of showings per room = S
N = 50   # number of seats per room = N

def stress_test1(session, number_of_actions=100):
    print("Stress Test 1 in progress...")
    # Create an intitial reservation
    user_id = uuid4()
    reservation_counts = {user_id: 0}
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    success_count = 0
    date = str(tomorrow.date()) # Tomorrow's date
    
    for i in range(number_of_actions):
        if make_reservation(session, user_id, "A6", date, "08:00", 1, reservation_counts):
            success_count += 1
    print(f"Reservations made: {success_count}") # If the number of reservations made != 1 then the seat was already occupied or the test was not successful
    print("Stress Test 1 completed.")

def stress_test2(session, repetitions, num_clients):
    print("Stress Test 2 in progress...")
    threads = []

    for i in range(num_clients):
        user_id = uuid4()  # Unique user ID for each client
        t = threading.Thread(target=client_task, args=(session, user_id, repetitions))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    
    print("Stress Test 2 completed.")

# task for each client in stress test 2
def client_task(session, user_id, repetitions):
    success_count = 0
    update_count = 0
    reservation_counts = {user_id: 0}
    # date
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    date = str(tomorrow.date()) # Tomorrow's date
    screenings = list(["A1", "A2", "A3", "A4", "A5", "A6", "A7"])
    for _ in range(repetitions):
        action = random.choice(["reserve", "update"])
        seat_number = random.randint(1, N+1)  # Assuming N seats per room
        
        if action == "reserve":
            time = random.choice(["08:00", "10:10", "12:20", "14:30", "16:40", "18:50", "21:00"])
            screening = random.choice(screenings)

            if make_reservation(session, user_id, screening, date, time, seat_number, reservation_counts):
                success_count += 1
        else:
            # Get a random reservation of the user to update
            reservation = session.execute("""
                SELECT reservation_id FROM reservations WHERE user_id = %s LIMIT 1 ALLOW FILTERING;
            """, (user_id,)).one()
            if reservation:
                if update_reservation(session, reservation.reservation_id, seat_number):
                    update_count += 1
                    
    print(f"Client {user_id} finished. Reservations made: {success_count}, Updates made: {update_count}")

def stress_test_3(session, num_clients, screening_details):
    print("Stress Test 3 in progress...")
    reserved_seats = {uuid4(): 0 for _ in range(num_clients)}
    threads = []

    for user_id in reserved_seats.keys():
        t = threading.Thread(target=reserve_max, args=(session, user_id, screening_details, reserved_seats))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("Stress Test 3 completed.")

# task for each client in stress test 3
def reserve_max(session, user_id, screening_details, reserved_seats):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    date = str(tomorrow.date())  # Tomorrow's date

    for room_name, room_id, screening_time in screening_details:
        # Convert screening_time to the required format HH:MM
        time = screening_time.strftime('%H:%M')
        for seat_number in range(1, N + 1):
            make_reservation(session, user_id, room_name, date, time, seat_number, reserved_seats)

    count = session.execute("SELECT COUNT(*) FROM reservations WHERE user_id = %s;", (user_id,)).one()[0]
    print(f"Reservations made by client {user_id}: {count}")

def main():
    cluster, session = get_session()  # Get the session
    delete_all_screenings_and_related_data(session)  # Delete all screenings and related data
    screening_details = create_screenings(session)  # Create screenings for all rooms and get details

    # decide which stress test to run
    print("Stress Test 1: The client makes the same request very quickly min (10000 times).")
    print("Stress Test 2: Two or more clients make the possible requests randomly (10000 times).")
    print("Stress Test 3: Immediate occupancy of all seats/reservations by 2 clients.")
    choice = input("Enter your choice: ")

    # measure the time taken to run the stress test
    start_time = datetime.now()

    if choice == '1':
        stress_test1(session, 10000)  # 10000 repetitions

    elif choice == '2':
        stress_test2(session, 5000, 2)  # 2 clients, 5000 repetitions each
    
    elif choice == '3':  
        stress_test_3(session, 2, screening_details)  # 2 clients, pass screening details
    
    # measure the time taken to run the stress test
    end_time = datetime.now()
    print(f"Time taken: {end_time - start_time}")

    # delete all screenings and related data that was produced during the stress test
    print("Deleting all screenings and related data that was produced during the tress test...")
    delete_all_screenings_and_related_data(session)

    session.shutdown()
    cluster.shutdown()

if __name__ == '__main__':
    main()