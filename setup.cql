DROP KEYSPACE IF EXISTS cinema_reservation;

CREATE KEYSPACE IF NOT EXISTS cinema_reservation
WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };

USE cinema_reservation;

CREATE TABLE IF NOT EXISTS rooms (
    room_id UUID PRIMARY KEY,
    name TEXT,
    num_seats INT
);

CREATE TABLE IF NOT EXISTS screenings (
    screening_id UUID,
    room_id UUID,
    screening_time TIMESTAMP,
    PRIMARY KEY (room_id, screening_time)
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id UUID,
    user_id UUID,
    screening_id UUID,
    seat_number INT,
    reservation_time TIMESTAMP,
    PRIMARY KEY (screening_id, seat_number)
);

CREATE INDEX IF NOT EXISTS ON reservations (reservation_id);
CREATE INDEX IF NOT EXISTS ON rooms (name);
CREATE INDEX IF NOT EXISTS user_id_idx ON reservations (user_id);

INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A1', 50);
INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A2', 50);
INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A3', 50);
INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A4', 50);
INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A5', 50);
INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A6', 50);
INSERT INTO rooms (room_id, name, num_seats) VALUES (uuid(), 'A7', 50);
