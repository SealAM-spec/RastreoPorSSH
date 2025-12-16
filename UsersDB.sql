drop database if exists usuarios;

create database if not exists usuarios;

use usuarios;

create table usuarios(
id int auto_increment primary key not null,
usuario varchar(15) not null,
contraseña varchar(20) not null
);

insert into usuarios(usuario, contraseña) values
('admin', 'rm401fbc'),
('user', 'c1sc0l0ver'),
('dameaccesow', 'porfavor');


select * from usuarios;