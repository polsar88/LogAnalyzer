class EmptyHeapException(Exception):
    '''This exception is raised when there is an attempt to pop an object from an empty heap.'''
    pass


class Heap:

    def __init__(self):
        self.heap = []
        self.obj2idx = {}


    def getNumObjs(self):
        '''Returns the number of objects in the heap.'''

        return len(self.heap)


    def addObj(self, obj, count = 1):
        '''Adds the passed hashable object to the heap, or if it already exists in the heap, increments its count by "count".'''

        if obj in self.obj2idx:
            idx = self.obj2idx[obj]
            self.heap[idx][1] += count
        else:
            idx = len(self.heap)
            self.heap.append([obj, count])  # We use list instead of tuple here because tuples are immutable.
            self.obj2idx[obj] = idx
        self.updateHeap(idx)


    def getMaxObjs(self, numObjs):
        '''Returns a dict of "numObjs" objects with the highest counts (or fewer if the size of the heap is less than "numObjs").'''

        dct = {}
        for i in range(numObjs):
            try:
                obj, count = self.popMaxObj()
                dct[obj] = count
            except EmptyHeapException:
                break

        # Now we need to re-insert the popped objects. This still results in O(k log n) running time, where "k = numObjs" and n is the heap size.
        for obj, count in dct.items():
            self.addObj(obj, count)

        return dct


    def popMaxObj(self):
        '''Returns an object with the maximum count together with its count. Raises EmptyHeapException if the heap is empty.'''

        if len(self.heap) == 0:
            raise EmptyHeapException

        obj, count = self.heap[0]
        del self.obj2idx[obj]
        elem = self.heap.pop()
        if len(self.heap) > 0:
            self.heap[0] = elem  # Place the last heap element in the newly vacated position.
            self.obj2idx[self.heap[0][0]] = 0  # This is not strictly necessary, since "updateHeap()" will update the map.
            self.updateHeap(0)
        return (obj, count)


    def updateHeap(self, idx):
        '''Updates heap at the specified index, which is the only index that may violate the heap invariant.'''

        if idx == 0 or self.heap[idx][1] < self.heap[(idx - 1) >> 1][1]:
            # Element at "idx" is the first element in the heap or it is smaller than its parent. Therefore, it can only go down.
            newIdx = self.bubbleDown(idx)
        else:
            newIdx = self.bubbleUp(idx)
        self.obj2idx[self.heap[newIdx][0]] = newIdx


    def bubbleDown(self, idx):
        while True:
            # Choose the greater child.
            leftChildIdx = 2 * idx + 1
            if leftChildIdx >= len(self.heap):
                break
            rightChildIdx = leftChildIdx + 1
            childIdx = rightChildIdx if (rightChildIdx < len(self.heap) and self.heap[rightChildIdx][1] > self.heap[leftChildIdx][1]) else leftChildIdx

            if self.heap[childIdx][1] > self.heap[idx][1]:
                self.heap[idx], self.heap[childIdx] = self.heap[childIdx], self.heap[idx]
                idx = childIdx
            else:
                break
        return idx


    def bubbleUp(self, idx):
        while idx > 0:
            parentIdx = (idx - 1) >> 1
            if self.heap[idx][1] > self.heap[parentIdx][1]:
                self.heap[idx], self.heap[parentIdx] = self.heap[parentIdx], self.heap[idx]
                idx = parentIdx
            else:
                break
        return idx
