/* Inserts a few devices, groups, and lights into the table */

insert into device values
	('913a8d11f5c5', '151.13.80.15', 'Device 1'),
	('45a4feaaceb3', '159.19.22.90', 'Device 2');

insert into "group" values 
	(1, 'Group 1', null), 
	(2, 'Group 2', 1), 
	(3, 'Group 3', 1), 
	(4, 'Group 4', 1);

insert into light values 
	(1, 2, 'Light 1', '913a8d11f5c5', 1),
	(2, 2, 'Light 2', '913a8d11f5c5', 2),
	(3, 2, 'Light 3', '913a8d11f5c5', 3),
	(4, 3, 'Light 4', '913a8d11f5c5', 4),
	(5, 3, 'Light 5', '45a4feaaceb3', 1),
	(6, 3, 'Light 6', '45a4feaaceb3', 2),
	(7, 4, 'Light 7', '45a4feaaceb3', 3),
	(8, 4, 'Light 8', '45a4feaaceb3', 4);