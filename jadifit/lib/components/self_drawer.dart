import 'package:flutter/material.dart';
import 'package:jadi_fit_app/components/self_drawer_tile.dart';
import 'package:jadi_fit_app/pages/settings_page.dart';

class MyDrawer extends StatefulWidget {
  const MyDrawer({super.key});

  @override
  State<MyDrawer> createState() => _MyDrawer();
}

class _MyDrawer extends State<MyDrawer> {
  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: Theme.of(context).colorScheme.surface,
      child: Column(
        children: [
          //app logo
          Padding(
            padding: const EdgeInsets.only(top: 100.0),
            child: Icon(
              Icons.lock_open_rounded,
              size: 75,
              color: Theme.of(context).colorScheme.inversePrimary
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(25.0),
            child: Divider(
              color: Theme.of(context).colorScheme.secondary
            )
          ),

          //home tile
          MyDrawerTile(
            text: 'H O M E', 
            icon: Icons.home, 
            onTap: () => Navigator.pop(context)
            ),

          //settings tile
          MyDrawerTile(
            text: 'S E T T I N G S', 
            icon: Icons.settings, 
            onTap: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) =>  const SettingsPage(),
                )
              );
            }
          ),

          const Spacer(),

          //logout list tile
          MyDrawerTile(
            text: 'L O G  O U T', 
            icon: Icons.logout, 
            onTap: () {}
            ),

          const SizedBox(height: 20.0)
        ],
      )
    );
  }
}