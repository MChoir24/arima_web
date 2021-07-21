DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS type_user;

CREATE TABLE type_user (
  id INTEGER PRIMARY KEY,
  type_name varchar(30) NOT NULL
);

INSERT INTO type_user (id, type_name) VALUE (0, 'type0');
INSERT INTO type_user (id, type_name) VALUE (1, 'type1');

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username varchar(30) UNIQUE NOT NULL,
  password varchar(100) NOT NULL,
  type_id INTEGER NOT NULL,
  FOREIGN KEY (type_id) REFERENCES type_user (id)
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title varchar(30) NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);