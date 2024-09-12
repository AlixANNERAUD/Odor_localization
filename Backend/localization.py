import numpy
from scipy.optimize import least_squares, minimize
from scipy.spatial import Delaunay

def triangulation(points, weights):
    """
    Triangulation algorithm

    # Arguments

    - points (numpy.ndarray of shape (n, 2)): points
    - weights (numpy.ndarray of shape (n,)): weights

    # Returns

    - numpy.ndarray of shape (2,): position    
    """

    # Create the Delaunay triangulation
    triangles = Delaunay(points)

    # Find the triangle that contains the point
    triangle_index = triangles.find_simplex(weights)

    # Get the triangle vertices
    triangle = triangles.simplices[triangle_index]

    # Get the triangle points
    triangle_points = points[triangle]

    # Calculate the barycentric coordinates
    barycentric = numpy.linalg.solve(triangle_points.T, weights - triangle_points[0])

    # Calculate the position
    position = numpy.dot(barycentric, triangle_points)

    return position
    

def trilateration(sensors, shifts):
    """
    Trilateration algorithm based on TDOA (Time Difference of Arrival) and the least squares optimization

    # Arguments

    - points (numpy.ndarray of shape (n, 2)): points
    - time_differences (numpy.ndarray of shape (n,)): time differences
    - function (function): function to optimize

    # Returns

    - numpy.ndarray of shape (2,): position
    """

    positions = numpy.zeros((len(sensors), 2))
    sshifts = numpy.zeros(len(sensors))

    for i, sensor_name in enumerate(shifts):
        print(f"Sensor name: {sensor_name}")

        positions[i] = sensors[sensor_name].get_position()
        sshifts[i] = shifts[sensor_name]

    print(f"Positions: {positions}")

    print(f"Shifts: {sshifts}")

    # Define the equations function to optimize/solve
    def error_function(params, positions, shifts):
        def distance_squared(x, y, x_i, y_i):
            return (x - x_i)**2 + (y - y_i)**2

        x_source, y_source, k = params
        error = 0
        x_ref, y_ref = positions[0]
        t_ref = shifts[0]
        
        for (x_i, y_i), t_i in zip(positions[1:], shifts[1:]):
            d_ref = numpy.sqrt(distance_squared(x_source, y_source, x_ref, y_ref))
            d_i = numpy.sqrt(distance_squared(x_source, y_source, x_i, y_i))
            predicted_time_diff = (d_i - d_ref) / k

            #print(f"t_ref: {t_ref}, t_i: {t_i}, predicted_time_diff: {predicted_time_diff}")

            actual_time_diff = numpy.sqrt(t_i) - numpy.sqrt(t_ref)
            error += (predicted_time_diff - actual_time_diff) ** 2
        
        return error

    # Define the initial guess as the mean of all points
    initial_guess = numpy.mean(positions, axis=0)
    initial_guess = numpy.append(initial_guess, 1)

    # Optimize/solve the equations
    result = minimize(error_function, initial_guess, args=(positions, sshifts), method='Nelder-Mead')

    return result.x