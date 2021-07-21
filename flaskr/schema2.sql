DROP TABLE IF EXISTS hasil_peramalan;
DROP TABLE IF EXISTS produksi;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS user_type;

CREATE TABLE user_type (
  id_type INTEGER PRIMARY KEY,
  type_name varchar(30) NOT NULL
);

INSERT INTO user_type (id_type, type_name) VALUE (0, 'user');
INSERT INTO user_type (id_type, type_name) VALUE (1, 'admin');

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username varchar(30) UNIQUE NOT NULL,
  password varchar(100) NOT NULL,
  id_type INTEGER NOT NULL,
  FOREIGN KEY (id_type) REFERENCES user_type (id_type)
);

CREATE TABLE hasil_peramalan (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  periode DATE NOT NULL,
  nilai FLOAT NOT NULL
);

CREATE TABLE produksi (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  periode DATE NOT NULL,
  nilai FLOAT NOT NULL
);