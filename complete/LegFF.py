import math
import time
import numpy as np

from jointdrive import JointDrive



class Leg:
    def __init__(self, legNumber, alphaID, betaID, gammaID, ccwAlpha, ccwBeta, ccwGamma):  # Konstruktor

        # Member Variable erstellen
        self.timefinished = time.time()
        self.legNumber = legNumber
        self.oldAngles = [0.0, 0.0, 0.0]  # Winkel zwischenspeichern (Geschwindigkeit der Servomotoren)
        self.lastPosition = [0, 0, 0, 1]

        # Abstände (Offsets) der Beinansatzpunkte s. Folien 2 und 4, werden übergeben
        self.xB = (0.033, 0.033, 0.000, -0.033, -0.033, 0.000)  # kurze Seite L1,L2,L4,L5
        self.yB = (-0.032, 0.032, 0.0445, 0.032, -0.032, -0.0445)  # lange Seite L3, L6

        # Abstände aN: a0 nur bei L3,6 und L1,2,4,5 gleich, s. Foliensatz L2
        if legNumber == 3 or legNumber == 6:

            self.legDistances = [0.032, 0.038, 0.049, 0.059, 0.021, 0.013, 0.092]

        else:

            self.legDistances = [0.042, 0.038, 0.049, 0.059, 0.021, 0.013, 0.092]

        # Berechnung Coxa, Femur, Tibia
        self.lc = self.legDistances[2]  # lc = a2
        self.lcSquare = math.pow(self.lc, 2)

        self.lf = math.sqrt(math.pow(self.legDistances[3], 2) + math.pow(self.legDistances[4], 2))
        self.lfSquare = math.pow(self.lf, 2)

        self.lt = math.sqrt(math.pow(self.legDistances[5], 2) + math.pow(self.legDistances[6], 2))
        self.ltSquare = math.pow(self.lt, 2)

        print("LC: ", self.lc, self.lcSquare)
        print("LF: ", self.lf, self.lfSquare)
        print("LT: ", self.lt, self.ltSquare)

        self.jointDriveBroadcast = JointDrive(id=254)
        self.jointDriveAlpha = JointDrive(id=alphaID, aOffset= 0, ccw = ccwAlpha)
        self.jointDriveBeta = JointDrive(id=betaID, aOffset= 0.34, ccw = ccwBeta)
        self.jointDriveGamma = JointDrive(id=gammaID, aOffset= 1.09, ccw = ccwGamma)
        self.oldAngles = [self.jointDriveAlpha.getCurrentJointAngle(), self.jointDriveBeta.getCurrentJointAngle(),
                          self.jointDriveGamma.getCurrentJointAngle()]


    def invKinAlphaJoint(self, pos=[0, 0, 0,1]):  # Bestimmung der Gelenkwinkel basierend auf der Position des Fußpunktes im Alphakoordinatensystem

        try:
            alpha = math.atan2(pos[1], pos[0])

            footPos = np.array(pos)
            A1 = np.array([
                [math.cos(alpha), 0, math.sin(alpha), self.lc * math.cos(alpha)],
                [math.sin(alpha), 0, -math.cos(alpha), self.lc * math.sin(alpha)],
                [0, 1, 0, 0],
                [0, 0, 0, 1]])

            betaPos = np.dot(A1, np.transpose([0, 0, 0, 1]))
            lct = np.linalg.norm(footPos[0:3] - betaPos[0:3])
            lctSquare = math.pow(lct, 2)
            gamma = math.acos((self.ltSquare + self.lfSquare - lctSquare) / (2 * self.lt * self.lf)) - math.pi

            h1 = math.acos((self.lfSquare + lctSquare - self.ltSquare) / (2 * self.lf * lct))
            h2 = math.acos(
                (lctSquare + self.lcSquare - math.pow(np.linalg.norm(footPos[0:3]), 2)) / (2 * self.lc * lct))

            # Falls Z Koordinate negativ
            if footPos[2] < 0:

                beta = (h1 + h2) - math.pi

            else:

                beta = (math.pi - h2) + h1

            return [alpha, beta, gamma]

        except Exception as e:

            print("Fehler in der Rueckwaertskinematik! Der Punkt liegt ausserhalb des Arbeitsbereiches! " + str(e))

            return self.oldAngles

    def forKinAlphaJoint(self, alpha, beta, gamma):  # Position des FUSSPUNKTS Alphakoordinatensystem

        try:

            T03LastColumn = np.array([
                [math.cos(alpha) * (self.lt * math.cos(beta + gamma) + self.lf * math.cos(beta) + self.lc)],
                [math.sin(alpha) * (self.lt * math.cos(beta + gamma) + ( self.lf * math.cos(beta) - self.legDistances[4]) + self.lc)], # NEU: - self.legDistances[4]!!!!!!!!!
                [self.lt * math.sin(beta + gamma) + self.lf * math.sin(beta)],
                [1]])

            return T03LastColumn

        except Exception as e:

            print("Fehler in der Vorwaertskinematik! " + str(e))


    def forCalcFootPoint(self, alpha, beta, gamma):  # die Position des Fußes ausgehend vom Alphakoordinatensystem

        T03 = self.forKinAlphaJoint(alpha, beta, gamma)

        return [T03[0, 0], T03[1, 0], T03[2, 0], 1]

    def setJointAngles(self, alpha, beta, gamma):

        footPositionAlpha = self.forCalcFootPoint(alpha, beta, gamma)  # Alphakoordinatensystem
        fPa = footPositionAlpha.copy()
        footPositionBasis = self.calcRotation_Z_Axis_OffsetBasisKoord( fPa)  # Berechnung der Fußposition in das Basiskoordinatensystem
        self.lastPosition = footPositionBasis.copy()
        print(self.lastPosition)
        self.setFootPosAngle(footPositionAlpha, footPositionBasis)  # Roboterbasiskoordinatensystem

    def calcRotation_Z_Axis_OffsetAlphaKoord(self, pos=[0.0, 0.0, 0.0, 1]):  # Offsets berechnen, um Punkte im Alphakoordinatensystem darzustellen

        if self.legNumber == 3:  # Rotation um 90 Grad

            minusSinusTheta = 1
            sinTheta = -1
            x = minusSinusTheta * pos[1]
            y = sinTheta * pos[0]
            pos[0] = x
            pos[1] = y

        elif self.legNumber == 6:  # Rotation um -90 Grad

            minusSinusTheta = -1
            sinTheta = 1
            x = minusSinusTheta * pos[1]
            y = sinTheta * pos[0]
            pos[0] = x
            pos[1] = y

        elif self.legNumber == 4 or self.legNumber == 5:  # Rotation um +- 180 Grad

            cosTheta = -1
            x = cosTheta * pos[0]
            y = cosTheta * pos[1]
            pos[0] = x
            pos[1] = y

        if self.legNumber == 1:

            pos[0] = pos[0] - self.xB[0] - self.legDistances[0]
            pos[1] -= self.yB[0]
            pos[2] += self.legDistances[1]
        elif self.legNumber == 2:

            pos[0] = pos[0] - self.xB[1] - self.legDistances[0]
            pos[1] -= self.yB[1]
            pos[2] += self.legDistances[1]

        elif self.legNumber == 3:

            pos[0] = pos[0] - self.yB[2] - self.legDistances[0]
            pos[1] += self.xB[2]
            pos[2] += self.legDistances[1]

        elif self.legNumber == 4:

            pos[0] = pos[0] + self.xB[3] - self.legDistances[0]
            pos[1] += self.yB[3]
            pos[2] += self.legDistances[1]

        elif self.legNumber == 5:

            pos[0] = pos[0] + self.xB[4] - self.legDistances[0]
            pos[1] += self.yB[4]
            pos[2] += self.legDistances[1]

        elif self.legNumber == 6:

            pos[0] = pos[0] + self.yB[5] - self.legDistances[0]
            pos[1] += self.xB[5]
            pos[2] += self.legDistances[1]
        return pos

    def calcRotation_Z_Axis_OffsetBasisKoord(self, pos=[0.0, 0.0, 0.0, 1]):  # Offsets berechnen, um Punkte im Basiskoordinatensystem darzustellen

        if self.legNumber == 6:  # Rotation um 90 Grad

            minusSinusTheta = 1
            sinTheta = -1
            x = minusSinusTheta * pos[1]
            y = sinTheta * pos[0]
            pos[0] = x
            pos[1] = y

        elif self.legNumber == 3:  # Rotation um -90 Grad

            minusSinusTheta = -1
            sinTheta = 1
            x = minusSinusTheta * pos[1]
            y = sinTheta * pos[0]
            pos[0] = x
            pos[1] = y

        elif self.legNumber == 4 or self.legNumber == 5:  # Rotation um +- 180 Grad

            cosTheta = -1
            x = cosTheta * pos[0]
            y = cosTheta * pos[1]
            pos[0] = x
            pos[1] = y

        if self.legNumber == 1:

            pos[0] = pos[0] + self.xB[0] + self.legDistances[0]
            pos[1] += self.yB[0]
            pos[2] -= self.legDistances[1]

        elif self.legNumber == 2:

            pos[0] = pos[0] + self.xB[1] + self.legDistances[0]
            pos[1] += self.yB[1]
            pos[2] -= self.legDistances[1]

        elif self.legNumber == 3:

            pos[0] += self.xB[2]
            pos[1] = pos[1] + self.yB[2] + self.legDistances[0]
            pos[2] -= self.legDistances[1]

        elif self.legNumber == 4:

            pos[0] = pos[0] - self.xB[3] + self.legDistances[0]
            pos[1] += self.yB[3]
            pos[2] -= self.legDistances[1]

        elif self.legNumber == 5:

            pos[0] = pos[0] - self.xB[4] + self.legDistances[0]
            pos[1] -= self.yB[4]
            pos[2] -= self.legDistances[1]

        elif self.legNumber == 6:

            pos[0] += self.xB[5]
            pos[1] = pos[1] + self.yB[5] - self.legDistances[0]
            pos[2] -= self.legDistances[1]
        return pos

    def setFootPosAngle(self, footPosAlpha=[0.0, 0.0, 0.0, 1], footPosBasis=[0.0, 0.0, 0.0, 1], speed=0):


        newAngles = self.invKinAlphaJoint(footPosAlpha)
        angleSpeed = self.calcServoSpeed(newAngles, self.oldAngles, 254)
        print(self.lastPosition)
        self.jointDriveAlpha.setDesiredAngleSpeed(newAngles[0], speed=angleSpeed[0], trigger=True)
        self.jointDriveBeta.setDesiredAngleSpeed(newAngles[1], speed=angleSpeed[1], trigger=True)
        self.jointDriveGamma.setDesiredAngleSpeed(newAngles[2], speed=angleSpeed[2], trigger=True)
        self.jointDriveBroadcast.action();

        self.oldAngles = footPosBasis
        print(self.lastPosition)

    def setFootPosPoints(self, footPos=[0.0, 0.0, 0.0, 1], speed = 1):

        footPosBasis = footPos.copy()
        self.lastPosition = footPosBasis.copy()
        newAngles = self.invKinAlphaJoint(self.calcRotation_Z_Axis_OffsetAlphaKoord(footPosBasis))
        angleSpeed = self.calcServoSpeed(newAngles, self.oldAngles, speed)
        succes, move_time = self.jointDriveAlpha.setDesiredAngleSpeed(newAngles[0], speed=angleSpeed[0], trigger=True)
        self.jointDriveBeta.setDesiredAngleSpeed(newAngles[1], speed=angleSpeed[1], trigger=True)
        self.jointDriveGamma.setDesiredAngleSpeed(newAngles[2], speed=angleSpeed[2], trigger=True)
        self.jointDriveBroadcast.action();
        self.timefinished += move_time

        self.oldAngles = newAngles.copy()

    # Reihenfolge der Winkel beachten! Differenz von neuen und alten Winkeln übergeben
    def calcServoSpeed(self, angles=[0.0, 0.0, 0.0], lastAngles=[0.0, 0.0, 0.0], speed=0):

        if angles == lastAngles:
            return [0,0,0]
        else:
            diffAngles = [abs(angles[0] - lastAngles[0]), abs(angles[1] - lastAngles[1]), abs(angles[2] - lastAngles[2])]
            largestAngle = max(diffAngles)

            alphaSpeed = (diffAngles[0] / largestAngle) * speed * 254
            betaSpeed = (diffAngles[1] / largestAngle) * speed * 254
            gammaSpeed = (diffAngles[2] / largestAngle) * speed * 254

            return [alphaSpeed, betaSpeed, gammaSpeed]

    def getlastPosition(self):
        return self.lastPosition

    def getTimefinished(self):
        return self.timefinished

