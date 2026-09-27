import 'package:flutter/material.dart';

class MyDescription extends StatelessWidget {
  const MyDescription({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).colorScheme.secondary),
        borderRadius: BorderRadius.circular(8.0)
      ),
      padding: const EdgeInsets.all(25.0),
      margin: const EdgeInsets.only(left: 25.0, right: 25.0, bottom: 25.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          //How far the restaurant is from your current location
          Column(
            children: [
              Text('2 km'),
              Text('Distance to restaurant'),
            ],
          ),
          Column(
            children: [
              Text('50-60 mins'),
              Text('Time to restaurant'),
            ],
          ),
        ]
      )
    );
  }
}