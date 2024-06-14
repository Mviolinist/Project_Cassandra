import sys
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from time import sleep
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement

R = 7   # number of rooms = R
S = 7   # number of showings per room = S
N = 50   # number of seats per room = N

def get_session():
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect('cinema_reservation')
    return cluster, session

def create_screenings(session):
    rooms = session.execute("SELECT room_id, name FROM rooms;")
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)
    screening_details = []
    for room in rooms:
        for i in range(S):  # S number of showings
            screening_time = start_time + timedelta(minutes=i * 130)  # 2 hours movie and 10 minutes break interval
            existing_screening = session.execute("""
                SELECT screening_id FROM screenings WHERE room_id = %s AND screening_time = %s;
            """, (room.room_id, screening_time)).one()
            if not existing_screening:
                session.execute("""
                    INSERT INTO screenings (screening_id, room_id, screening_time)
                    VALUES (uuid(), %s, %s)
                """, (room.room_id, screening_time))
                print(f"Created screening for room {room.name} at {screening_time}")
                screening_details.append((room.name, room.room_id, screening_time))
    return screening_details

def make_reservation(session, user_id, room_name, date, time, seat_number, reservation_counts):
    # Parse the screening time
    screening_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    # Check if the screening exists
    room = session.execute("SELECT room_id FROM rooms WHERE name = %s;", (room_name,)).one() # room must be correct, ensured earlier
    screening = session.execute("""
        SELECT screening_id FROM screenings WHERE room_id = %s AND screening_time = %s;
    """, (room.room_id, screening_time)).one()
    if not screening:
        print("Screening not found!")
        return None
    
    # Check if the seat is already occupied
    reservation = session.execute("""
        SELECT reservation_id FROM reservations WHERE screening_id = %s AND seat_number = %s;
    """, (screening.screening_id, seat_number)).one()
    if reservation:
        #print("Seat already occupied!")
        return None

    # Try to make a reservation
    try:
        reservation_id = uuid4()
        reservation_time = datetime.now()
        query = SimpleStatement("""
        INSERT INTO reservations (reservation_id, user_id, screening_id, seat_number, reservation_time)
        VALUES (%s, %s, %s, %s, %s)
        """, consistency_level=ConsistencyLevel.ALL)
        session.execute(query, (reservation_id, user_id, screening.screening_id, seat_number, reservation_time))
        reservation_counts[user_id] += 1
        return reservation_id
    except Exception as e:
        print(f"Failed to make reservation!:\n {e}")
        return False

def update_reservation(session, reservation_id, new_seat_number):
    # invalid reservation id
    reservation = session.execute("SELECT * FROM reservations WHERE reservation_id = %s;", (reservation_id,)).one()
    if not reservation:
        print("Reservation not found!")
        return False
    
    # Check if the new seat is already occupied
    seat = session.execute("SELECT reservation_id FROM reservations WHERE screening_id = %s AND seat_number = %s;", (reservation.screening_id, new_seat_number)).one()
    if seat:
        #print("Seat already occupied!")
        return False

    # Create a new reservation with the new seat number
    try:
        # make new reservation
        new_reservation_id = uuid4()
        reservation_time = datetime.now()
        query = SimpleStatement("""
            INSERT INTO reservations (reservation_id, user_id, screening_id, seat_number, reservation_time)
            VALUES (%s, %s, %s, %s, %s)
        """, consistency_level=ConsistencyLevel.ALL)
        session.execute(query, (new_reservation_id, reservation.user_id, reservation.screening_id, new_seat_number, reservation_time))

        # delete old reservation
        try:
            delete_query = SimpleStatement("""
                DELETE FROM reservations WHERE screening_id = %s AND seat_number = %s;
            """, consistency_level=ConsistencyLevel.ALL)
            session.execute(delete_query, (reservation.screening_id, reservation.seat_number))
        except Exception as e:
            print(f"Failed to delete the old reservation!:\n {e}")
            return False

        return new_reservation_id # return new reservation id
    
    except Exception as e:
        print(f"Failed to create a new reservation!:\n {e}")
        return False

def view_reservation(session, reservation_id):
    reservations = session.execute("SELECT * FROM reservations WHERE reservation_id = %s;", (reservation_id,))
    if not reservations:
        return "Reservation not found!"
    screenings = {row.screening_id: row for row in session.execute("SELECT * FROM screenings;")}
    rooms = {row.room_id: row for row in session.execute("SELECT * FROM rooms;")}
    
    for reservation in reservations:
        screening = screenings.get(reservation.screening_id)
        if screening:
            room = rooms.get(screening.room_id)
            if room:
                room_name = room.name
                screening_time = screening.screening_time.strftime('%Y-%m-%d %H:%M')
                seat_number = reservation.seat_number
                reservation_id = reservation.reservation_id
                reservation_time = reservation.reservation_time.strftime('%Y-%m-%d %H:%M:%S')
                user_id = reservation.user_id
                output = (f"Room: {room_name}, Time: {screening_time}, Seat: {seat_number}, Reservation ID: {reservation_id}, Reservation Time: {reservation_time}, User ID: {user_id}")
                return output
            
def view_available_seats(session, room_name, date, time):
    screening_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    room = session.execute("SELECT room_id FROM rooms WHERE name = %s;", (room_name,)).one()
    if not room:
        print("Room not found!")
        return []

    screening = session.execute("""
        SELECT screening_id FROM screenings WHERE room_id = %s AND screening_time = %s;
    """, (room.room_id, screening_time)).one()
    if not screening:
        print("Screening not found!")
        return []

    reserved_seats = session.execute("""
        SELECT seat_number FROM reservations WHERE screening_id = %s;
    """, (screening.screening_id,)).all()
    reserved_seat_numbers = {row.seat_number for row in reserved_seats}
    all_seats = set(range(1, N+1))  # Only N seats
    available_seats = all_seats - reserved_seat_numbers
    return list(available_seats)

def main():
    cluster, session = get_session()
    user_id = uuid4()  # Assume a new user for each session
    reservation_counts = {user_id: 0}

    def print_menu():
        print("\nCinema Reservation System")
        print("1. Make a Reservation")
        print("2. Update a Reservation")
        print("3. View a Reservation")
        print("4. View Available Seats")
        print("5. Exit")
        choice = input("Enter your choice: ")
        return choice

    screening_details = create_screenings(session)  # Create screenings for all rooms

    while True:
        choice = print_menu()

        if choice == '1':
            room_name = input("Enter room name (A1-A7): ")
            # DEFAULT OPTION for faster testing
            if room_name == "":
                room_name = "A1"
            # wrong room name
            elif room_name not in ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]:
                print("Invalid room name. Please try again.")
                continue

            date = input("Enter date (YYYY-MM-DD): ")
            # DEFAULT OPTION for faster testing
            if date == "":
                date = "2024-06-15"
            # wrong date format
            elif len(date) != 10 or date[4] != '-' or date[7] != '-' or not date[:4].isdigit() or not date[5:7].isdigit() or not date[8:].isdigit():
                print("Invalid date format. Please try again.")
                continue

            time = input("Enter time (HH:MM): ")
            # DEFAULT OPTION for faster testing
            if time == "":
                time = "08:00"
            # wrong time format
            elif len(time) != 5 or time[2] != ':' or not time[:2].isdigit() or not time[3:].isdigit():
                print("Invalid time format. Please try again.")
                continue

            seat_number = int(input("Enter seat number (1-50): "))
            # DEFAULT OPTION for faster testing
            if seat_number == "":
                seat_number = 1
            # wrong seat number
            elif seat_number not in range(1, N+1):
                print("Invalid seat number. Please try again.")
                continue

            reservation_id = make_reservation(session, user_id, room_name, date, time, seat_number, reservation_counts)
            if reservation_id:
                print(f"Reservation created with ID: {reservation_id}")

        elif choice == '2':
            reservation_id = UUID(input("Enter reservation ID: "))
            new_seat_number = int(input("Enter new seat number (1-180): "))
            new_reservation_id = update_reservation(session, reservation_id, new_seat_number)
            if new_reservation_id:
                print(f"Reservation updated with new ID: {new_reservation_id}")

        elif choice == '3':
            reservation_id = UUID(input("Enter reservation ID: "))
            reservation = view_reservation(session, reservation_id)
            print(f"Reservation Details: {reservation}")

        elif choice == '4':
            room_name = input("Enter room name (A1-A8): ")
            date = input("Enter date (YYYY-MM-DD): ")
            time = input("Enter time (HH:MM): ")
            available_seats = view_available_seats(session, room_name, date, time)
            print(f"Available Seats: {available_seats}")

        elif choice == '5':
            break
        
        else:
            print("Invalid choice. Please try again.")

    session.shutdown()
    cluster.shutdown()

if __name__ == '__main__':
    main()
