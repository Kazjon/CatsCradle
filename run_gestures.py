
from ActionModule import ActionModule
from time import sleep


if __name__ == "__main__":
    action_module = ActionModule(1920, 1080, dummy=False)

    action_module.goBackToZero()
    while not action_module.checkTargetReached():
        pass
    sleep(2)

    emotional_gestures = {e:[[],[]] for e in ['surprise', 'shame', 'longing', 'fear']}
    emotional_gestures["neutral"] = [[],[]]
    for e, gestures_and_weights in emotional_gestures.iteritems():
        for name, weight_and_sequence in action_module.gestureNameToSeq.iteritems():
            if name.startswith(e):
                weight = weight_and_sequence[0]
                sequence = weight_and_sequence[1]
                gestures_and_weights[0].append(weight)
                gestures_and_weights[1].append(sequence)
    # Now we know how many gestures are in each category, divide the weight for each by the number to get a probability.
    gestures_and_weights[0] = [w/sum(gestures_and_weights[0]) for w in gestures_and_weights[0]]

    # run all the gestures
    emotion_name = 'shame'
    for index, gesture in enumerate(emotional_gestures[emotion_name][1]):

        action_module.executeGesture(gesture, useThread=True)
        while not action_module.checkTargetReached():
            pass
            # sleep(3)
        raw_input()
        action_module.goBackToZero()
        while not action_module.checkTargetReached():
            pass
        raw_input()
            # sleep(3)
            # if index > 4:
            #     break


    # action_module.executeGesture(emotional_gestures[emotion_name][1][4])
    # while not action_module.checkTargetReached():
    #     pass
    # sleep(2)
