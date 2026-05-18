-- Run AFTER you have a user row.
-- Replace :user_id with your actual users.id (e.g. SELECT id FROM users WHERE telegram_id = 123;)

insert into meal_presets (user_id, name, kcal, protein_g, carbs_g, fat_g, emoji, sort_order) values
  (:user_id, 'Protein Shake',         150,  25,  8, 3, '🥤',  1),
  (:user_id, 'Meal Replace. Shake',   200,  20, 24, 5, '🥛',  2),
  (:user_id, 'Steamed Egg',            80,   8,  1, 5, '🥚',  3),
  (:user_id, 'Congee (plain)',        120,   3, 25, 1, '🍚',  4),
  (:user_id, 'Steamed Fish',          150,  28,  0, 4, '🐟',  5),
  (:user_id, 'Stir-fry Veg',           90,   3, 10, 4, '🥬',  6),
  (:user_id, 'Tofu Soup',             100,  10,  4, 5, '🍲',  7),
  (:user_id, 'Brown Rice (½ cup)',    110,   3, 23, 1, '🍙',  8),
  (:user_id, 'Boiled Chicken',        165,  31,  0, 4, '🍗',  9),
  (:user_id, 'Wonton Soup',           180,  12, 20, 5, '🥟', 10),
  (:user_id, 'Green Tea',               0,   0,  0, 0, '🍵', 11),
  (:user_id, 'Fruit Fibre Shake',     285,   5, 55, 4, '🍓', 12),
  (:user_id, 'Scallion Pancake',      270,   5, 35,12, '🧅', 13);
