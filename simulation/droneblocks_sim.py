from DroneBlocksTelloSimulator.DroneBlocksSimulatorContextManager import DroneBlocksSimulatorContextManager

if __name__ == '__main__':

    sim_key = '8dce0fea-7ba9-40c5-adc8-4ec80aaf5720'
    distance = 40
    with DroneBlocksSimulatorContextManager(simulator_key=sim_key) as drone:
        drone.takeoff()
        drone.fly_forward(distance, 'in')
        drone.fly_left(distance, 'in')
        drone.fly_backward(distance, 'in')
        drone.fly_right(distance, 'in')
        drone.flip_backward()
        drone.land()