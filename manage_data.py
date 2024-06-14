from cassandra.cluster import Cluster
from uuid import UUID

def get_session():
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect('cinema_reservation')
    return cluster, session

def show_all_reservations(session):
    reservations = session.execute("SELECT * FROM reservations;")
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
                print(f"Room: {room_name}, Time: {screening_time}, Seat: {seat_number}, Reservation ID: {reservation_id}, Reservation Time: {reservation_time}, User ID: {user_id}")

def delete_all_reservations(session):
    session.execute("TRUNCATE reservations;")
    print("All reservations have been deleted.")

def delete_all_screenings_and_related_data(session):
    session.execute("TRUNCATE reservations;")
    session.execute("TRUNCATE screenings;")
    print("All screenings and related reservations have been deleted.")

def show_all_screenings(session):
    screenings = session.execute("SELECT * FROM screenings;")
    rooms = {row.room_id: row for row in session.execute("SELECT * FROM rooms;")}
    for screening in screenings:
        room = rooms.get(screening.room_id)
        if room:
            room_name = room.name
            screening_time = screening.screening_time.strftime('%Y-%m-%d %H:%M')
            print(f"Room: {room_name}, Time: {screening_time}")

def show_reservation_count(session):
    count = session.execute("SELECT COUNT(*) FROM reservations;").one()[0]
    print(f"All reservations made: {count}")

def show_reservation_count_by_client(session, user_id):
    count = session.execute("SELECT COUNT(*) FROM reservations WHERE user_id = %s;", (user_id,)).one()[0]
    print(f"Reservations made by client {user_id}: {count}")

def main():
    cluster, session = get_session()

    def print_menu():
        print("\nManage Reservations")
        print("1. Show all Reservations")
        print("2. Delete all Reservations")
        print("3. Delete all Screenings and related Reservations")
        print("4. Show all Screenings")
        print("5. Exit")
        print("6. Show number of all made reservations")
        print("7. Show number of reservations made by the given client")
        choice = input("Enter your choice: ")
        return choice

    while True:
        choice = print_menu()

        if choice == '1':
            show_all_reservations(session)
        elif choice == '2':
            delete_all_reservations(session)
        elif choice == '3':
            delete_all_screenings_and_related_data(session)
        elif choice == '4':
            show_all_screenings(session)
        elif choice == '5':
            break
        elif choice == '6':
            show_reservation_count(session)
        elif choice == '7':
            user_id = UUID(input("Enter client user ID: "))
            show_reservation_count_by_client(session, user_id)
        else:
            print("Invalid choice. Please try again.")

    session.shutdown()
    cluster.shutdown()

if __name__ == '__main__':
    main()